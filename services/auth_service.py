from typing import TYPE_CHECKING, Optional, Dict, Any
import os
import secrets
import string
import hashlib
import datetime
from datetime import timedelta, UTC
from utils.time_utils import now
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
from models.user_auth import UserAuth, Session
from constants import Roles
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from database_manager import DatabaseManager

class AuthService:
    def __init__(self, db: "DatabaseManager"):
        self.db = db
        self.token_expiry = timedelta(days=1)  # 1 day token expiry
        self.passwords_file = "users_passwords.json"
        
    async def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_hex(32)
    
    async def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password with guaranteed character types"""
        if length < 8:
            length = 8  # Minimum length for security
            
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*()_-+=<>?"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters
        all_chars = uppercase + lowercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - len(password)))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)
    
    async def create_user_password(self, user_id: int, role: int) -> Optional[str]:
        """Create a password for a user if they don't have one yet"""
        try:
            print(f"Creating password for user {user_id} with role {role}")
            if role != Roles.LPR:
                return None
                
            async with self.db.Session() as session:
                # Check if user already has a password
                result = await session.execute(select(UserAuth).filter_by(user_id=user_id))
                user_auth = result.scalars().first()
                
                if user_auth:
                    return None  # User already has a password
                
                # Generate a new password
                password = await self.generate_password()
                password_hash = await self.hash_password(password)
                
                # Create user auth entry
                new_auth = UserAuth(user_id=user_id, password_hash=password_hash)
                session.add(new_auth)
                await session.commit()
                
                # Add to passwords file
                await self._save_password_to_file(user_id, password)
                
                return password
                
        except SQLAlchemyError as e:
            print(f"Error in create_user_password: {e}")
            return None
    
    async def _save_password_to_file(self, user_id: int, password: str) -> None:
        """Save password to a file for admin reference"""
        passwords = {}
        
        # Load existing passwords if file exists
        if os.path.exists(self.passwords_file):
            try:
                with open(self.passwords_file, 'r') as f:
                    passwords = json.load(f)
            except json.JSONDecodeError:
                passwords = {}
        
        # Add or update password
        passwords[str(user_id)] = password
        
        # Write passwords to file
        with open(self.passwords_file, 'w') as f:
            json.dump(passwords, f, indent=2)
    
    async def verify_password(self, user_id: int, password: str) -> bool:
        """Verify a user's password"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(UserAuth).filter_by(user_id=user_id))
                user_auth = result.scalars().first()
                
                if not user_auth:
                    return False
                
                password_hash = await self.hash_password(password)
                return password_hash == user_auth.password_hash
                
        except SQLAlchemyError as e:
            print(f"Error in verify_password: {e}")
            return False
    
    async def login(self, username: str, password: str, ip_address: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and create a session"""
        try:
            async with self.db.Session() as session:
                # Find user by username
                result = await session.execute(select(User).filter_by(username=username))
                user = result.scalars().first()
                
                if not user:
                    return None
                
                # Check password
                if not await self.verify_password(user.id, password):
                    return None
                
                # Generate a token
                token = await self.generate_token()
                expires_at = now() + self.token_expiry
                
                # Create a new session
                new_session = Session(
                    user_id=user.id,
                    token=token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=expires_at
                )
                
                session.add(new_session)
                await session.commit()
                
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "token": token,
                    "expires_at": expires_at.isoformat(),
                    "role": user.role
                }
                
        except SQLAlchemyError as e:
            print(f"Error in login: {e}")
            return None
    
    async def verify_token(self, token: str, ip_address: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """Verify a token and return user information"""
        try:
            async with self.db.Session() as session:
                # Find session by token
                result = await session.execute(select(Session).filter_by(token=token, is_active=True))
                session_obj = result.scalars().first()
                
                if not session_obj:
                    return None
                
                # Check if session is expired - convert naive datetime to timezone-aware if needed
                current_time = now()
                expires_at = session_obj.expires_at
                
                # Make sure expires_at is timezone-aware
                if expires_at.tzinfo is None:
                    # Convert naive datetime to tz-aware
                    expires_at = expires_at.replace(tzinfo=UTC)
                    
                if expires_at < current_time:
                    session_obj.is_active = False
                    await session.commit()
                    return None
                
                # Verify IP and user agent
                if session_obj.ip_address != ip_address or session_obj.user_agent != user_agent:
                    return None
                
                # Get the user
                user_result = await session.execute(select(User).filter_by(id=session_obj.user_id))
                user = user_result.scalars().first()
                
                if not user:
                    return None
                
                # Update last activity
                session_obj.last_activity = now()
                await session.commit()
                
                # Return user information
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "token": token,
                    "expires_at": session_obj.expires_at,
                    "role": user.role
                }
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def logout(self, token: str) -> bool:
        """Log out a user by deactivating their session"""
        try:
            async with self.db.Session() as session:
                # Find session by token
                result = await session.execute(select(Session).filter_by(token=token))
                session_obj = result.scalars().first()
                
                if not session_obj:
                    return False
                
                # Set session as inactive
                session_obj.is_active = False
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error in logout: {e}")
            return False
    
    async def generate_passwords_for_admins(self):
        """Generate passwords for all users with admin role if they don't have one"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(User).filter_by(role=Roles.LPR))
                admin_users = result.scalars().all()
                print(f"Found {len(admin_users)} admin users")
                for user in admin_users:
                    await self.create_user_password(user.id, user.role)
                
        except SQLAlchemyError as e:
            print(f"Error in generate_passwords_for_admins: {e}")
    
    async def list_active_sessions(self, user_id: Optional[int] = None) -> list:
        """List all active sessions, optionally filtered by user_id"""
        try:
            async with self.db.Session() as session:
                query = select(Session).filter_by(is_active=True)
                
                if user_id is not None:
                    query = query.filter_by(user_id=user_id)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except SQLAlchemyError as e:
            logger.error(f"Error in list_active_sessions: {e}")
            return []
    
    async def terminate_session(self, session_id: int) -> bool:
        """Terminate a specific session"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Session).filter_by(id=session_id))
                session_obj = result.scalars().first()
                
                if not session_obj:
                    return False
                
                session_obj.is_active = False
                await session.commit()
                return True
                
        except SQLAlchemyError as e:
            print(f"Error in terminate_session: {e}")
            return False 
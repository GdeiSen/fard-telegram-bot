from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from .base import Base

from utils.time_utils import now, now_for_db

class UserAuth(Base):
    __tablename__ = 'user_auth'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=lambda: now())
    updated_at = Column(DateTime, default=lambda: now(), onupdate=lambda: now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    def __init__(self, user_id: int, password_hash: str):
        self.user_id = user_id
        self.password_hash = password_hash


class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    token = Column(String(256), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: now())
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=lambda: now())
    
    user = relationship("User", foreign_keys=[user_id])
    
    def __init__(self, user_id: int, token: str, ip_address: str, 
                 user_agent: str, expires_at: datetime):
        self.user_id = user_id
        self.token = token
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = expires_at 
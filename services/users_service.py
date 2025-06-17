from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from contextlib import asynccontextmanager  
from models.user import User

if TYPE_CHECKING:
    from database_manager import DatabaseManager

class UsersService:
    def __init__(self, db : "DatabaseManager"):
        self.db = db

    async def get_user(self, user_id: int) -> "User | None":
        try:
            async with self.db.Session() as session:  
                result = await session.execute(select(User).filter_by(id=user_id))  
                user = result.scalars().first() 
                return user
        except SQLAlchemyError as e:
            print(f"Error in get_user: {e}")
            return None

    async def create_user(self, user: "User") -> "User | None":
        try:
            async with self.db.Session() as session: 
                result = await session.execute(select(User).filter_by(id=user.id))
                existing_user = result.scalars().first()

                if existing_user:
                    return await self.update_user(user)  

                session.add(user)  
                await session.commit() 
                return await self.get_user(user.id)  
        except SQLAlchemyError as e:
            print(f"Error in create_user: {e}")
            return None

    async def update_user(self, user: "User") -> "User | None":
        try:
            async with self.db.Session() as session:
                await session.merge(user) 
                await session.commit()
                return await self.get_user(user.id) 
        except SQLAlchemyError as e:
            print(f"Error in update_user: {e}")
            return None

    async def delete_user(self, user: "User") -> bool:
        try:
            async with self.db.Session() as session:
                await session.delete(user) 
                await session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Error in delete_user: {e}")
            return False

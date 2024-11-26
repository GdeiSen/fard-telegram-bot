from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database
    from models import User

class UsersService:
    def __init__(self, db):
        self.db : Database = db

    async def get_user(self, user_id: int) -> "User | None":
        user = await self.db.get_user(user_id)
        if user:
            return user
        return None

    async def create_user(self, user: "User") -> "User":
        test = await self.db.get_user(user.id)
        if test:
            return await self.update_user(user)
        await self.db.insert_user(user)
        return user

    async def update_user(self, user: "User") -> "User":
        await self.db.update_user(user)
        return user

    async def remove_user(self, user: "User"):
        await self.db.remove_user(user)

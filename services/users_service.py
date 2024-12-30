from typing import TYPE_CHECKING
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import user_to_model, model_to_user

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    
from entities.user import User

from models import UserModel, user_to_model, model_to_user

class UsersService:
    def __init__(self, db: "DatabaseManager"):
        self.db: DatabaseManager = db

    async def get_user(self, user_id: int) -> "User | None":
        try:
            session: Session = self.db.session
            user_model = session.query(UserModel).filter_by(id=user_id).first()
            if user_model:
                user = model_to_user(user_model)
                return user
            return None
        except SQLAlchemyError as e:
            print(f"Error in get_user: {e}")
            return None

    async def create_user(self, user: "User") -> "User":
        try:
            user_model = user_to_model(user)
            session: Session = self.db.session
            existing_user_model = session.query(UserModel).filter_by(id=user_model.id).first()
            if existing_user_model:
                return await self.update_user(user)
            session.add(user_model)
            session.commit()
            return user
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in create_user: {e}")
            return user

    async def update_user(self, user: "User") -> "User":
        try:
            user_model = user_to_model(user)
            session: Session = self.db.session
            session.merge(user_model)
            session.commit()
            return user
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in update_user: {e}")
            return user

    async def delete_user(self, user: "User"):
        try:
            user_model = user_to_model(user)
            session: Session = self.db.session
            session.delete(user_model)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in remove_user: {e}")

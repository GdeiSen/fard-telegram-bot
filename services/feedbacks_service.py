from typing import TYPE_CHECKING, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from models import Feedback

if TYPE_CHECKING:
    from database_manager import DatabaseManager


class FeedbacksService:
    def __init__(self, db: "DatabaseManager"):
        self.database_manager = db

    async def create_feedback(self, feedback: Feedback) -> Optional[Feedback]:
        try:
            async with self.database_manager.Session() as session:
                # Проверка на существующий feedback
                result = await session.execute(
                    select(Feedback).filter_by(id=feedback.id)
                )
                existing_feedback = result.scalars().first()
                if existing_feedback:
                    return await self.update_feedback(feedback)

                feedback.id = None
                session.add(feedback)
                await session.commit()

                return await self.get_feedback(feedback.id)
        except SQLAlchemyError as e:
            print(f"Error in create_feedback: {e}")
            return None

    async def update_feedback(self, feedback: Feedback) -> Optional[Feedback]:
        try:
            async with self.database_manager.Session() as session:
                await session.merge(feedback)
                await session.commit()

                return await self.get_feedback(feedback.id)
        except SQLAlchemyError as e:
            print(f"Error in update_feedback: {e}")
            return None

    async def delete_feedback(self, feedback: Feedback) -> bool:
        try:
            async with self.database_manager.Session() as session:
                await session.delete(feedback)
                await session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Error in delete_feedback: {e}")
            return False

    async def get_feedback(self, feedback_id: int) -> Optional[Feedback]:
        try:
            async with self.database_manager.Session() as session:
                result = await session.execute(
                    select(Feedback).filter_by(id=feedback_id)
                )
                feedback = result.scalars().first()
                return feedback
        except SQLAlchemyError as e:
            print(f"Error in get_feedback: {e}")
            return None

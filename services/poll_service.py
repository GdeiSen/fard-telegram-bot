from typing import List, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from models import PollAnswer

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    from models import User
    from entities.dialog_answer import Answer


class PollService:
    def __init__(self, db: "DatabaseManager"):
        self.db = db

    async def insert_answer(self, user: "User", answer: "Answer") -> None:
        try:
            async with self.db.Session() as session:
                answer.user_id = user.id
                answer.id = None
                poll_answer = PollAnswer(
                    id=None,
                    user_id=user.id,
                    dialog_id=answer.dialog_id,
                    sequence_id=answer.sequence_id,
                    item_id=answer.item_id,
                    answer=answer.answer
                )
                session.add(poll_answer)
                await session.commit()
        except SQLAlchemyError as e:
            print(f"Error in insert_answer: {e}")

    async def update_answer(self, user: "User", answer: "Answer") -> None:
        try:
            async with self.db.Session() as session:
                answer.user_id = user.id
                result = await session.execute(
                    select(PollAnswer).filter_by(
                        user_id=user.id,
                        dialog_id=answer.dialog_id,
                        sequence_id=answer.sequence_id,
                        item_id=answer.item_id
                    )
                )
                existing_answer = result.scalars().first()
                if existing_answer is None:
                    await self.insert_answer(user, answer)
                else:
                    existing_answer.answer = answer.answer
                    await session.commit()
        except SQLAlchemyError as e:
            print(f"Error in update_answer: {e}")

    async def get_answers(self, user: "User") -> List["Answer"]:
        try:
            async with self.db.Session() as session:
                result = await session.execute(
                    select(PollAnswer).filter_by(user_id=user.id)
                )
                answers = result.scalars().all()
                return answers
        except SQLAlchemyError as e:
            print(f"Error in get_answers: {e}")
            return []

from typing import TYPE_CHECKING, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import user_to_model, model_to_user, poll_answer_to_model, model_to_poll_answer

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    from entities.user import User
    from entities.answer import Answer
    
from models import UserModel, PollAnswerModel
    
class PollService:
    def __init__(self, db: "DatabaseManager"):
        self.db: DatabaseManager = db

    async def insert_answer(self, user: "User", answer: "Answer"):
        try:
            answer.user_id = user.id
            answer.id = None
            poll_answer_model = poll_answer_to_model(answer)
            session: Session = self.db.session
            session.add(poll_answer_model)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in insert_answer: {e}")

    async def update_answer(self, user: "User", answer: "Answer"):
        try:
            answer.user_id = user.id
            poll_answer_model = poll_answer_to_model(answer)
            session: Session = self.db.session
            existing_answer = session.query(PollAnswerModel).filter_by(
                user_id=user.id,
                dialog_id=answer.dialog_id,
                sequence_id=answer.sequence_id,
                item_id=answer.item_id
            ).first()
            if existing_answer is None:
                await self.insert_answer(user, answer)
            else:
                poll_answer_model.id = existing_answer.id
                session.merge(poll_answer_model)
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in update_answer: {e}")

    async def get_answers(self, user: "User") -> "List[Answer]":
        try:
            session: Session = self.db.session
            answer_models = session.query(PollAnswerModel).filter_by(user_id=user.id).all()
            answers = [model_to_poll_answer(model) for model in answer_models]
            return answers
        except SQLAlchemyError as e:
            print(f"Error in get_answers: {e}")
            return []

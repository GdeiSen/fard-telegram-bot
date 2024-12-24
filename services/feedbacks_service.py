from typing import TYPE_CHECKING
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    
from models import FeedbackModel, feedback_to_model, model_to_feedback

class FeedbacksService:
    def __init__(self, db: "DatabaseManager"):
        self.database_manager: DatabaseManager = db

    async def create_feedback(self, feedback: "FeedbackModel") -> "FeedbackModel":
        try:
            session: Session = self.database_manager.session
            feedback_model = feedback_to_model(feedback)
            existing_feedback = session.query(FeedbackModel).filter_by(id=feedback_model.id).first()
            if existing_feedback:
                return await self.update_feedback(feedback_model)
            feedback_model.id = None
            session.add(feedback_model)
            session.commit()
            return self.get_feedback(feedback_model.id)
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in create_feedback: {e}")
            return feedback

    async def update_feedback(self, feedback: "FeedbackModel") -> "FeedbackModel":
        try:
            session: Session = self.database_manager.session
            feedback_model = feedback_to_model(feedback)
            session.merge(feedback_model)
            session.commit()
            return self.get_feedback(feedback_model.id)
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in update_feedback: {e}")
            return feedback

    async def delete_feedback(self, feedback: "FeedbackModel"):
        try:
            session: Session = self.database_manager.session
            feedback_model = feedback_to_model(feedback)
            session.delete(feedback_model)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in remove_feedback: {e}")

    async def get_feedback(self, feedback_id: int) -> "FeedbackModel | None":
        try:
            session: Session = self.database_manager.session
            feedback_model = session.query(FeedbackModel).filter_by(id=feedback_id).first()
            if feedback_model:
                feedback = model_to_feedback(feedback_model)
                return feedback
            return None
        except SQLAlchemyError as e:
            print(f"Error in get_feedback: {e}")
            return None

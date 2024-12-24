from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.feedback import Feedback
from .base import Base

class FeedbackModel(Base):
    __tablename__ = 'feedbacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    dialog_id = Column(Integer, nullable=False)
    sequence_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    answer = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("UserModel", back_populates="feedbacks")
    
def feedback_to_model(feedback: Feedback) -> FeedbackModel:
    return FeedbackModel(
        id=feedback.id,
        user_id=feedback.user_id,
        dialog_id=feedback.dialog_id,
        sequence_id=feedback.sequence_id,
        item_id=feedback.item_id,
        answer=feedback.answer
    )

def model_to_feedback(feedback_model: FeedbackModel) -> Feedback:
    return Feedback(
        id=feedback_model.id,
        user_id=feedback_model.user_id,
        dialog_id=feedback_model.dialog_id,
        sequence_id=feedback_model.sequence_id,
        item_id=feedback_model.item_id,
        answer=feedback_model.answer,
        created_at=feedback_model.created_at,
        updated_at=feedback_model.updated_at
    )
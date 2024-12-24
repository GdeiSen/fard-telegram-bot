from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.dialog_answer import Answer
from .base import Base

class PollAnswerModel(Base):
    __tablename__ = 'poll_answers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    dialog_id = Column(Integer, nullable=False)
    sequence_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    answer = Column(String(255), nullable=False)
    
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("UserModel", back_populates="poll_answers")
    
def poll_answer_to_model(answer: Answer) -> PollAnswerModel:
    return PollAnswerModel(
        id=answer.id,
        user_id=answer.user_id,
        dialog_id=answer.dialog_id,
        sequence_id=answer.sequence_id,
        item_id=answer.item_id,
        answer=answer.answer
    )

def model_to_poll_answer(poll_answer: PollAnswerModel) -> Answer:
    return Answer(
        id=poll_answer.id,
        user_id=poll_answer.user_id,
        dialog_id=poll_answer.dialog_id,
        sequence_id=poll_answer.sequence_id,
        item_id=poll_answer.item_id,
        answer=poll_answer.answer,
        created_at=poll_answer.created_at,
        updated_at=poll_answer.updated_at
    )
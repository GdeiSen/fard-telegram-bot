from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.dialog_answer import Answer
from .base import Base

from utils.time_utils import now, now_for_db

class PollAnswer(Base, Answer):
    __tablename__ = 'poll_answers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    dialog_id = Column(Integer, nullable=False)
    sequence_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    answer = Column(String(255), nullable=False)
    
    details = Column(Text)
    created_at = Column(DateTime, default=now_for_db)
    updated_at = Column(DateTime, default=now_for_db, onupdate=now_for_db)
    user = relationship("User", back_populates="poll_answers")
    
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, item_id: int, 
                answer: str, details: str = None, created_at: datetime = None, updated_at: datetime = None):
        Answer.__init__(self, id, user_id, dialog_id, sequence_id, item_id, answer, created_at, updated_at)
        self.details = details
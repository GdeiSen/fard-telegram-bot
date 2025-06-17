from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.dialog_answer import Answer
from .base import Base

from utils.time_utils import now, now_for_db

class ServiceTicket(Base, Answer):
    __tablename__ = 'service_tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    image = Column(String(1000))
    status = Column(Integer, default=0)
    
    dialog_id = Column(Integer)
    sequence_id = Column(Integer)
    item_id = Column(Integer)
    answer = Column(String(2000))
    
    header = Column(String(1000), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_for_db)
    updated_at = Column(DateTime, default=now_for_db, onupdate=now_for_db)
    user = relationship("User", back_populates="service_tickets")
    
    # Добавляем связь со статусами заявки
    statuses = relationship("ServiceTicketStatus", back_populates="ticket", cascade="all, delete-orphan")
    
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, item_id: int, 
                answer: str, description: str, location: str, image: str | None = None, 
                status: int = 0, details: str = None, header: str = None, 
                created_at: datetime = None, updated_at: datetime = None):
        Answer.__init__(self, id, user_id, dialog_id, sequence_id, item_id, answer, created_at, updated_at)
        self.description = description
        self.location = location
        self.image = image
        self.status = status
        self.details = details
        self.header = header

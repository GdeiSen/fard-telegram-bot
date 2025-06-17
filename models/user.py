from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, UTC
from .base import Base

from utils.time_utils import now, now_for_db

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    username = Column(String(150), nullable=True)
    role = Column(Integer, nullable=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    middle_name = Column(String(50))
    language_code = Column(String(2), default="ru")
    data_processing_consent = Column(Boolean, default=False)
    object = Column(String(500))
    legal_entity = Column(String(500))
    phone_number = Column(String(40))
    email = Column(String(100))
    
    created_at = Column(DateTime, default=lambda: now())
    updated_at = Column(DateTime, default=lambda: now(), onupdate=lambda: now())
    service_tickets = relationship("ServiceTicket", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    poll_answers = relationship("PollAnswer", back_populates="user")
    space_views = relationship("SpaceView", back_populates="user")
    
    def __init__(self, id: int, username: str, role: int | None):
        self.id = id
        self.username = username
        self.role = role
        self.first_name = None
        self.last_name = None
        self.middle_name = None
        self.language_code = "ru"
        self.data_processing_consent = False
        self.object = None
        self.legal_entity = None
        self.phone_number = None
        self.email = None
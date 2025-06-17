from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

from utils.time_utils import now, now_for_db

class Object(Base):
    __tablename__ = 'objects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    photos = Column(JSON, default=list)
    created_at = Column(DateTime, default=now_for_db)
    updated_at = Column(DateTime, default=now_for_db, onupdate=now_for_db)
    
    # Связь с помещениями (spaces)
    spaces = relationship("Space", back_populates="object", cascade="all, delete-orphan")
    
    def __init__(self, id: int, name: str, address: str, description: str, photos: list[str] = None, created_at: datetime = None, updated_at: datetime = None):
        self.id = id
        self.name = name
        self.address = address
        self.description = description
        self.photos = photos or []
        self.created_at = created_at
        self.updated_at = updated_at 
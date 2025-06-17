from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

from utils.time_utils import now, now_for_db

class Space(Base):
    __tablename__ = 'spaces'
    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey('objects.id'), nullable=False)
    floor = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    photos = Column(JSON, default=list)
    is_available = Column(Boolean, default=True)
    status = Column(Boolean, default=True)  # True - опубликовано, False - скрыто
    created_at = Column(DateTime, default=now_for_db)
    updated_at = Column(DateTime, default=now_for_db, onupdate=now_for_db)
    
    # Связь с объектом недвижимости
    object = relationship("Object", back_populates="spaces")
    
    # Связь с просмотрами
    views = relationship("SpaceView", back_populates="space", cascade="all, delete-orphan")
    
    def __init__(self, id: int, object_id: int, floor: str, size: int, description: str, 
                 photos: list[str] = None, is_available: bool = True, status: bool = True,
                 created_at: datetime = None, updated_at: datetime = None):
        self.id = id
        self.object_id = object_id
        self.floor = floor
        self.size = size
        self.description = description
        self.photos = photos or []
        self.is_available = is_available
        self.status = status  # True - опубликовано, False - скрыто
        self.created_at = created_at
        self.updated_at = updated_at 
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

from utils.time_utils import now, now_for_db

class SpaceView(Base):
    __tablename__ = 'space_views'
    id = Column(Integer, primary_key=True, autoincrement=True)
    space_id = Column(Integer, ForeignKey('spaces.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    view_date = Column(DateTime, default=now_for_db)
    created_at = Column(DateTime, default=now_for_db)
    
    # Связь с помещением
    space = relationship("Space", back_populates="views")
    
    # Связь с пользователем
    user = relationship("User")
    
    def __init__(self, id: int, space_id: int, user_id: int, 
                 view_date: datetime, created_at: datetime = None):
        self.id = id
        self.space_id = space_id
        self.user_id = user_id
        self.view_date = view_date
        self.created_at = created_at 
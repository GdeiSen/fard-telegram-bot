from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.user import User
from .base import Base

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    role = Column(Integer, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    middle_name = Column(String)
    language_code = Column(String, default="ru")
    data_processing_consent = Column(Boolean, default=False)
    object = Column(String)
    legal_entity = Column(String)
    phone_number = Column(String)
    email = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    service_tickets = relationship("ServiceTicketModel", back_populates="user")
    feedbacks = relationship("FeedbackModel", back_populates="user")
    poll_answers = relationship("PollAnswerModel", back_populates="user")

def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        username=user.username,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        language_code=user.language_code,
        data_processing_consent=user.data_processing_consent,
        object=user.object,
        legal_entity=user.legal_entity,
        phone_number=user.phone_number,
        email=user.email
    )
    
def model_to_user(user_model: UserModel) -> User:
    user = User(
        id=user_model.id,
        username=user_model.username,
        role=user_model.role
    )
    user.first_name = user_model.first_name
    user.last_name = user_model.last_name
    user.middle_name = user_model.middle_name
    user.language_code = user_model.language_code
    user.data_processing_consent = user_model.data_processing_consent
    user.object = user_model.object
    user.legal_entity = user_model.legal_entity
    user.phone_number = user_model.phone_number
    user.email = user_model.email
    return user
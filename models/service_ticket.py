from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from entities.service_ticket import ServiceTicket
from .base import Base

class ServiceTicketModel(Base):
    __tablename__ = 'service_tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    image = Column(String(255))
    status = Column(Integer, default=0)
    
    dialog_id = Column(Integer)
    sequence_id = Column(Integer)
    item_id = Column(Integer)
    answer = Column(String(255))
    
    header = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("UserModel", back_populates="service_tickets")
    
def service_ticket_to_model(ticket: ServiceTicket) -> ServiceTicketModel:
    return ServiceTicketModel(
        id=ticket.id,
        user_id=ticket.user_id,
        description=ticket.description,
        location=ticket.location,
        image=ticket.image,
        status=ticket.status,
        dialog_id=ticket.dialog_id,
        sequence_id=ticket.sequence_id,
        item_id=ticket.item_id,
        answer=ticket.answer,
        header=ticket.header,
        details=ticket.details,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

def model_to_service_ticket(ticket_model: ServiceTicketModel) -> ServiceTicket:
    return ServiceTicket(
        id=ticket_model.id,
        user_id=ticket_model.user_id,
        description=ticket_model.description,
        location=ticket_model.location,
        image=ticket_model.image,
        status=ticket_model.status,
        dialog_id=ticket_model.dialog_id,
        sequence_id=ticket_model.sequence_id,
        item_id=ticket_model.item_id,
        answer=ticket_model.answer,
        header=ticket_model.header,
        details=ticket_model.details
    )

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from .base import Base

from utils.time_utils import now, now_for_db

class ServiceTicketStatus(Base):
    __tablename__ = 'service_ticket_statuses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('service_tickets.id'), nullable=False)
    status_type = Column(Integer, nullable=False)  # 1 - Принято, 2 - Передано, 3 - Выполнено
    assignee = Column(String(255), nullable=True)  # Фамилия исполнителя (для статуса "Передано")
    created_at = Column(DateTime, default=now_for_db)
    admin_id = Column(BigInteger, nullable=True)  # ID администратора который обработал заявку
    message_id = Column(BigInteger, nullable=True)  # ID сообщения в чате админов
    
    # Обратная связь с ServiceTicket
    ticket = relationship("ServiceTicket", back_populates="statuses")

# Дополним ServiceTicket в models/service_ticket.py отношением
# statuses = relationship("ServiceTicketStatus", back_populates="ticket") 
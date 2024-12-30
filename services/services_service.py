from typing import TYPE_CHECKING, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    
from models import ServiceTicketModel, service_ticket_to_model, model_to_service_ticket
from entities.service_ticket import ServiceTicket

class ServicesService:
    def __init__(self, db: "DatabaseManager"):
        self.db: DatabaseManager = db

    def get_service_tickets(self, user_id: int) -> "List[ServiceTicket]":
        try:
            session: Session = self.db.session
            service_ticket_models = session.query(ServiceTicketModel).filter_by(user_id=user_id).all()
            service_tickets = [service_ticket_to_model(model) for model in service_ticket_models]
            return service_tickets
        except SQLAlchemyError as e:
            print(f"Error in get_service_tickets: {e}")
            return []

    def create_service_ticket(self, service: "ServiceTicket") -> "ServiceTicket":
        try:
            session: Session = self.db.session
            service_model = service_ticket_to_model(service)
            service_model.id = None
            existing_service = session.query(ServiceTicketModel).filter_by(id=service_model.id).first()
            if existing_service:
                return self.update_service_ticket(service_model)
            service_model.id = None
            session.add(service_model)
            session.commit()
            return self.get_service_ticket(service_model.id)
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in create_service_ticket: {e}")
            raise e
            return service

    def update_service_ticket(self, service: "ServiceTicket") -> "ServiceTicket":
        try:
            session: Session = self.db.session
            service_model = service_ticket_to_model(service)
            session.merge(service_model)
            session.commit()
            return self.get_service_ticket(service_model.id)
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error in update_service_ticket: {e}")
            return service

    def get_service_ticket(self, service_id: int) -> "ServiceTicket | None":
        try:
            session: Session = self.db.session
            service_model = session.query(ServiceTicketModel).filter_by(id=service_id).first()
            if service_model:
                service = model_to_service_ticket(service_model)
                return service
            return None
        except SQLAlchemyError as e:
            print(f"Error in get_service_ticket: {e}")
            return None
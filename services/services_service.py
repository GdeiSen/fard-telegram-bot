from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import ServiceTicket, ServiceTicketStatus
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from utils.time_utils import now

if TYPE_CHECKING:
    from database_manager import DatabaseManager
    from managers.event_manager import EventManager

class ServicesService:
    def __init__(self, db: "DatabaseManager", event_manager: "EventManager" = None):
        self.db = db
        self.event_manager = event_manager

    async def get_service_tickets(self, user_id: int) -> List[ServiceTicket]:
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(ServiceTicket).filter_by(user_id=user_id))
                service_tickets = result.scalars().all()
                return service_tickets
        except SQLAlchemyError as e:
            print(f"Error in get_service_tickets: {e}")
            return []

    async def create_service_ticket(self, service: ServiceTicket) -> Optional[ServiceTicket]:
        try:
            async with self.db.Session() as session:
                service.id = None
                session.add(service)
                await session.commit()
                await session.refresh(service)
                
                # Уведомляем о создании нового тикета
                if self.event_manager:
                    await self.event_manager.emit('ticket_created', service)
                    await self.event_manager.emit('ticket_stats_changed')
                
                return service
        except SQLAlchemyError as e:
            print(f"Error in create_service_ticket: {e}")
            return None

    async def update_service_ticket(self, service: ServiceTicket) -> Optional[ServiceTicket]:
        try:
            async with self.db.Session() as session:
                await session.merge(service)
                await session.commit()
                return await self.get_service_ticket(service.id)
        except SQLAlchemyError as e:
            print(f"Error in update_service_ticket: {e}")
            return None

    async def get_service_ticket(self, service_id: int) -> Optional[ServiceTicket]:
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(ServiceTicket).filter_by(id=service_id))
                service = result.scalars().first()
                return service
        except SQLAlchemyError as e:
            print(f"Error in get_service_ticket: {e}")
            return None

    async def get_all_service_tickets(self) -> List[ServiceTicket]:
        """Получить все заявки на обслуживание"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(ServiceTicket))
                service_tickets = result.scalars().all()
                return service_tickets
        except SQLAlchemyError as e:
            print(f"Error in get_all_service_tickets: {e}")
            return []

    async def get_service_ticket_with_statuses(self, ticket_id: int):
        """Получить заявку вместе с историей статусов"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(
                    select(ServiceTicket).filter_by(id=ticket_id).options(
                        selectinload(ServiceTicket.statuses)
                    )
                )
                return result.scalars().first()
        except SQLAlchemyError as e:
            print(f"Error in get_service_ticket_with_statuses: {e}")
            return None

    async def add_ticket_status(self, ticket_id: int, status_type: int, admin_id: int, 
                               message_id: int = None, assignee: str = None) -> bool:
        """Добавить новый статус к заявке
        
        Args:
            ticket_id: ID заявки
            status_type: Тип статуса (1-Принято, 2-Передано, 3-Выполнено)
            admin_id: ID администратора
            message_id: ID сообщения в чате администраторов
            assignee: Фамилия исполнителя (для статуса "Передано")
        """
        try:
            async with self.db.Session() as session:
                # Проверяем существование заявки
                ticket_result = await session.execute(
                    select(ServiceTicket).filter_by(id=ticket_id)
                )
                ticket = ticket_result.scalars().first()
                
                if not ticket:
                    return False
                
                # Используем московское время для дат
                current_time = now()
                
                # Создаем новый статус
                new_status = ServiceTicketStatus(
                    id=None,
                    ticket_id=ticket_id,
                    status_type=status_type,
                    admin_id=admin_id,
                    message_id=message_id,
                    assignee=assignee,
                    created_at=current_time
                )
                
                # Обновляем общий статус заявки
                old_status = ticket.status
                ticket.status = status_type
                ticket.updated_at = current_time
                
                session.add(new_status)
                await session.commit()
                
                # Уведомляем об изменении статуса тикета
                if self.event_manager:
                    await self.event_manager.emit('ticket_status_changed', {
                        'ticket': ticket,
                        'old_status': old_status,
                        'new_status': status_type,
                        'assignee': assignee
                    })
                    await self.event_manager.emit('ticket_stats_changed')
                
                return True
                
        except SQLAlchemyError as e:
            print(f"Error in add_ticket_status: {e}")
            return False
            
    async def get_ticket_by_message_id(self, message_id: int):
        """Найти заявку по ID сообщения в чате администраторов"""
        try:
            async with self.db.Session() as session:
                status_result = await session.execute(
                    select(ServiceTicketStatus).filter_by(message_id=message_id)
                )
                status = status_result.scalars().first()
                
                if not status:
                    return None
                    
                ticket_result = await session.execute(
                    select(ServiceTicket).filter_by(id=status.ticket_id)
                )
                return ticket_result.scalars().first()
                
        except SQLAlchemyError as e:
            print(f"Error in get_ticket_by_message_id: {e}")
            return None

    async def get_tickets_statistics(self) -> dict:
        """Получить статистику тикетов по статусам"""
        try:
            async with self.db.Session() as session:
                # Получаем все тикеты
                result = await session.execute(select(ServiceTicket))
                tickets = result.scalars().all()
                
                # Подсчитываем статистику
                stats = {
                    'total_tickets': len(tickets),
                    'new_tickets': 0,
                    'accepted_tickets': 0,
                    'assigned_tickets': 0,
                    'completed_tickets': 0
                }
                
                for ticket in tickets:
                    if ticket.status == 0:  # Новые (созданные)
                        stats['new_tickets'] += 1
                    elif ticket.status == 1:  # Принятые
                        stats['accepted_tickets'] += 1
                    elif ticket.status == 2:  # Переданные
                        stats['assigned_tickets'] += 1
                    elif ticket.status == 3:  # Выполненные
                        stats['completed_tickets'] += 1
                
                return stats
                
        except SQLAlchemyError as e:
            print(f"Error in get_tickets_statistics: {e}")
            return {
                'total_tickets': 0,
                'new_tickets': 0,
                'accepted_tickets': 0,
                'assigned_tickets': 0,
                'completed_tickets': 0
            }

    async def get_detailed_tickets_statistics(self) -> dict:
        """Получить детальную статистику тикетов с ID заявок по статусам"""
        try:
            async with self.db.Session() as session:
                # Получаем все тикеты
                result = await session.execute(select(ServiceTicket))
                tickets = result.scalars().all()
                
                # Группируем по статусам
                new_tickets = []
                in_progress_tickets = []  # Принятые + Переданные
                
                for ticket in tickets:
                    if ticket.status == 0:  # Новые (непринятые)
                        new_tickets.append(ticket.id)
                    elif ticket.status in [1, 2]:  # Принятые или Переданные (в работе)
                        in_progress_tickets.append(ticket.id)
                    # Выполненные не включаем в статистику
                
                return {
                    'new_count': len(new_tickets),
                    'in_progress_count': len(in_progress_tickets),
                    'new_tickets': new_tickets,
                    'in_progress_tickets': in_progress_tickets
                }
                
        except SQLAlchemyError as e:
            print(f"Error in get_detailed_tickets_statistics: {e}")
            return {
                'new_count': 0,
                'in_progress_count': 0,
                'new_tickets': [],
                'in_progress_tickets': []
            }

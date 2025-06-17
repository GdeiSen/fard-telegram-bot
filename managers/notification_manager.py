from typing import TYPE_CHECKING, Optional
import json
import re
from datetime import datetime
from telegram.constants import ParseMode
from constants import Dialogs, ServiceTicketStatus
from .base_manager import BaseManager

from utils.time_utils import now, now_for_db

from telegram import Update, Message
from telegram.ext import ContextTypes
from models import ServiceTicket

if TYPE_CHECKING:
    from bot import Bot


class NotificationManager(BaseManager):
    """
    Менеджер для централизованного управления уведомлениями по заявкам.
    
    Отвечает за:
    - Уведомления администраторов о новых заявках
    - Обработку ответов администраторов
    - Уведомления клиентов о статусе заявок
    - Автоматическую отправку опросов качества
    """
    
    def __init__(self, bot: "Bot"):
        super().__init__(bot)
        self._admin_chat_id = None
        self._chief_engineer_chat_id = None
    
    async def initialize(self) -> None:
        """Инициализация менеджера уведомлений"""
        self._admin_chat_id = self.bot.managers.headers.get("ADMIN_CHAT_ID")
        self._chief_engineer_chat_id = self.bot.managers.headers.get("CHIEF_ENGINEER_CHAT_ID")
        print("NotificationManager initialized")
    
    async def notify_new_ticket(self, ticket: "ServiceTicket") -> Optional["Message"]:
        """
        Отправляет уведомление администраторам о новой заявке
        
        Args:
            ticket: Модель заявки
            
        Returns:
            Отправленное сообщение или None
        """
        try:
            if not self._admin_chat_id:
                print("Admin chat ID is not configured")
                return None
                
            # Получаем информацию о пользователе
            user = await self.bot.services.users.get_user(ticket.user_id)
            user_name = self.bot.get_text("unknown_user")
            if user:
                user_name = f"{user.last_name or ''} {user.first_name or ''} {user.middle_name or ''}".strip()
                
            # Извлекаем номер телефона из деталей заявки
            phone_number = self.bot.get_text("phone_not_specified")
            if ticket.details:
                details = json.loads(ticket.details)
                phone_number = details.get("phone_number", self.bot.get_text("phone_not_specified"))
                
            # Форматируем дату создания
            created_date = now().strftime("%d.%m.%Y %H:%M")
                
            # Формируем текст уведомления
            message_text = self.bot.get_text("ticket_to_admin_chat", [
                ticket.id,
                created_date,
                ticket.description or self.bot.get_text("description_not_specified"),
                ticket.location or self.bot.get_text("location_not_specified"),
                user_name,
                phone_number
            ])
            
            # Отправляем сообщение в чат администраторов
            message = await self.bot.application.bot.send_message(
                chat_id=self._admin_chat_id,
                text=message_text,
                parse_mode=ParseMode.HTML
            )
            
            # Сохраняем ID сообщения для связи с заявкой
            if message and message.message_id:
                await self.bot.services.tickets.add_ticket_status(
                    ticket_id=ticket.id,
                    status_type=0,  # Статус "Создана"
                    admin_id=None,
                    message_id=message.message_id
                )
                
            return message
            
        except Exception as e:
            print(f"Error sending ticket notification to admin chat: {e}")
            return None
    
    async def handle_admin_reply(self, update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> bool:
        """
        Обрабатывает ответы администраторов на сообщения о заявках
        
        Args:
            update: Обновление Telegram
            context: Контекст обработчика
            
        Returns:
            True если ответ был обработан, False иначе
        """
        try:
            # Проверяем, что это ответ на сообщение
            if not update.message or not update.message.reply_to_message:
                return False
                
            reply_to_message = update.message.reply_to_message
            admin_id = update.message.from_user.id if update.message.from_user else None
            
            # Находим заявку по ID сообщения
            ticket = await self.bot.services.tickets.get_ticket_by_message_id(
                reply_to_message.message_id
            )
            
            if not ticket:
                return False
                
            # Получаем текст ответа администратора
            message_text = update.message.text
            if not message_text:
                return False
            
            # Обрабатываем различные типы ответов
            if re.search(r'принят[оа]', message_text.lower()):
                await self._process_ticket_accepted(update, context, ticket, admin_id)
                return True
                
            # Обработка назначения исполнителя
            assigned_match = re.search(r'передан[оа]\s+["\']?([А-Яа-я]+)["\']?', message_text.lower())
            if not assigned_match:
                assigned_match = re.search(r'передал\s+["\']?([А-Яа-я]+)["\']?', message_text.lower())
                
            if assigned_match:
                assignee = assigned_match.group(1).strip().capitalize()
                await self._process_ticket_assigned(update, context, ticket, admin_id, assignee)
                return True
                
            # Обработка завершения заявки
            if re.search(r'выполнен[оа]', message_text.lower()):
                await self._process_ticket_completed(update, context, ticket, admin_id)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error handling admin reply: {e}")
            return False
    
    async def _process_ticket_accepted(self, update: "Update", context: "ContextTypes.DEFAULT_TYPE", 
                                     ticket, admin_id: int):
        """Обрабатывает принятие заявки администратором"""
        success = await self.bot.services.tickets.add_ticket_status(
            ticket_id=ticket.id,
            status_type=ServiceTicketStatus.ACCEPTED,
            admin_id=admin_id,
            message_id=update.message.message_id
        )
        
        if success:
            await self.bot.managers.message.reply_message(
                update, context, "ticket_accepted", payload=[ticket.id]
            )
    
    async def _process_ticket_assigned(self, update: "Update", context: "ContextTypes.DEFAULT_TYPE", 
                                     ticket, admin_id: int, assignee: str):
        """Обрабатывает передачу заявки исполнителю"""
        success = await self.bot.services.tickets.add_ticket_status(
            ticket_id=ticket.id,
            status_type=ServiceTicketStatus.ASSIGNED,
            admin_id=admin_id,
            assignee=assignee,
            message_id=update.message.message_id
        )
        
        if success:
            await self.bot.managers.message.reply_message(
                update, context, "ticket_assigned", payload=[ticket.id, assignee]
            )
    
    async def _process_ticket_completed(self, update: "Update", context: "ContextTypes.DEFAULT_TYPE", 
                                      ticket, admin_id: int):
        """Обрабатывает выполнение заявки"""
        success = await self.bot.services.tickets.add_ticket_status(
            ticket_id=ticket.id,
            status_type=ServiceTicketStatus.COMPLETED,
            admin_id=admin_id,
            message_id=update.message.message_id
        )
        
        if success:
            await self.bot.managers.message.reply_message(
                update, context, "ticket_completed", payload=[ticket.id]
            )
            
            # Автоматически уведомляем пользователя о выполнении и предлагаем оценить качество
            await self.notify_ticket_completion(ticket.id, ticket.user_id)
    
    async def notify_ticket_completion(self, ticket_id: int, user_id: int):
        """
        Уведомляет пользователя о выполнении заявки и предлагает оценить качество
        
        Args:
            ticket_id: ID завершенной заявки
            user_id: ID пользователя
        """
        try:
            # Создаем клавиатуру для запуска диалога обратной связи
            keyboard = self.bot.create_keyboard([
                [("rate_completion", f"{Dialogs.SERVICE_FEEDBACK}:{ticket_id}")]
            ])
            
            # Отправляем уведомление пользователю
            await self.bot.application.bot.send_message(
                chat_id=user_id,
                text=self.bot.get_text("ticket_completion_notification"),
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            print(f"Error notifying user about ticket completion: {e}")
    
    async def send_feedback_to_chief_engineer(self, ticket_id: int, feedback_message: str):
        """
        Отправляет обратную связь главному инженеру
        
        Args:
            ticket_id: ID заявки
            feedback_message: Текст обратной связи
        """
        try:
            if not self._chief_engineer_chat_id:
                print("Chief engineer chat ID is not configured")
                return
                
            # Получаем информацию о заявке
            ticket = await self.bot.services.tickets.get_service_ticket(ticket_id)
            if not ticket:
                print(f"Ticket not found: {ticket_id}")
                return
                
            # Получаем информацию о пользователе
            user = await self.bot.services.users.get_user(ticket.user_id)
            user_name = self.bot.get_text('service_feedback_unknown_user')
            if user:
                user_name = f"{user.last_name or ''} {user.first_name or ''} {user.middle_name or ''}".strip()
                
            # Получаем номер телефона из деталей заявки
            phone_number = self.bot.get_text('service_feedback_phone_not_specified')
            if ticket.details:
                details = json.loads(ticket.details)
                phone_number = details.get("phone_number", self.bot.get_text('service_feedback_phone_not_specified'))
                
            # Форматируем дату создания
            created_date = now().strftime("%d.%m.%Y %H:%M")
            
            # Формируем и отправляем сообщение
            message_text = self.bot.get_text('service_feedback_to_chief_engineer', [
                created_date,
                ticket.description or 'Не указана',
                ticket.location or 'Не указано',
                user_name,
                phone_number,
                feedback_message
            ])
            
            await self.bot.application.bot.send_message(
                chat_id=self._chief_engineer_chat_id,
                text=message_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            print(f"Error sending feedback to chief engineer: {e}")
    
    def is_admin_chat(self, chat_id: int) -> bool:
        """
        Проверяет, является ли чат административным
        
        Args:
            chat_id: ID чата
            
        Returns:
            True если это административный чат
        """
        return self._admin_chat_id and str(chat_id) == str(self._admin_chat_id) 
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TYPE_CHECKING
from zoneinfo import ZoneInfo
from .base_manager import BaseManager

from utils.time_utils import now, now_for_db

if TYPE_CHECKING:
    from bot import Bot


class StatsManager(BaseManager):
    """Менеджер для управления статистикой тикетов и автоматического обновления сообщений"""
    
    def __init__(self, bot: "Bot", json_file_path: str = "stats_data.json"):
        """
        Инициализация менеджера статистики
        
        Args:
            bot: Экземпляр бота
            json_file_path: Путь к JSON файлу для сохранения данных
        """
        super().__init__(bot)
        self.json_file_path = json_file_path
        self.moscow_tz = ZoneInfo("Europe/Moscow")
        self._ensure_json_file()
    
    async def initialize(self) -> None:
        """Инициализация менеджера статистики"""
        try:
            # Настраиваем обработчики событий
            self._setup_event_handlers()
            
            # Инициализируем сообщение со статистикой при запуске
            await self.initialize_stats_message()
            
            print("StatsManager initialized")
        except Exception as e:
            print(f"Error initializing StatsManager: {e}")
    
    def _ensure_json_file(self) -> None:
        """Создает JSON файл если он не существует"""
        if not os.path.exists(self.json_file_path):
            initial_data = {
                "stats_message": {
                    "chat_id": None,
                    "message_id": None,
                    "created_at": None,
                    "last_updated": None
                },
                "stats": {
                    "total_tickets": 0,
                    "new_tickets": 0,
                    "accepted_tickets": 0,
                    "assigned_tickets": 0,
                    "completed_tickets": 0,
                    "last_update": None
                },
                "detailed_stats": {
                    "new_count": 0,
                    "in_progress_count": 0,
                    "new_tickets": [],
                    "in_progress_tickets": [],
                    "last_update": None
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из JSON файла"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ensure_json_file()
            return self._load_data()
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Сохраняет данные в JSON файл"""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Error saving stats data: {e}")
    
    def save_message_info(self, chat_id: int, message_id: int) -> None:
        """Сохраняет информацию о сообщении со статистикой"""
        data = self._load_data()
        current_time = now()
        
        data["stats_message"] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "created_at": current_time.isoformat(),
            "last_updated": current_time.isoformat()
        }
        
        self._save_data(data)
    
    def get_message_info(self) -> Optional[Dict[str, Any]]:
        """Получает информацию о сообщении со статистикой"""
        data = self._load_data()
        message_info = data.get("stats_message", {})
        
        if not message_info.get("chat_id") or not message_info.get("message_id"):
            return None
            
        return message_info
    
    def is_message_expired(self, hours_limit: int = 48) -> bool:
        """Проверяет, истек ли срок редактирования сообщения"""
        message_info = self.get_message_info()
        if not message_info or not message_info.get("created_at"):
            print("Message info not found or no created_at timestamp")
            return True
            
        try:
            created_at = datetime.fromisoformat(message_info["created_at"])
            current_time = now()
            
            # Убеждаемся, что время создания также в московском часовом поясе
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=self.moscow_tz)
            
            time_diff = current_time - created_at
            is_expired = time_diff > timedelta(hours=hours_limit)
            
            print(f"Message age check: created={created_at.strftime('%d.%m.%Y %H:%M')}, "
                  f"current={current_time.strftime('%d.%m.%Y %H:%M')}, "
                  f"age={time_diff}, limit={hours_limit}h, expired={is_expired}")
            
            return is_expired
        except Exception as e:
            print(f"Error checking message expiration: {e}")
            return True
    
    def update_stats(self, stats: Dict[str, int]) -> None:
        """Обновляет статистику тикетов"""
        data = self._load_data()
        current_time = now()
        
        # Получаем текущую статистику для сравнения
        current_stats = data.get("stats", {})
        
        # Проверяем, изменилась ли статистика
        stats_changed = False
        for key in ['total_tickets', 'new_tickets', 'accepted_tickets', 'assigned_tickets', 'completed_tickets']:
            if current_stats.get(key, 0) != stats.get(key, 0):
                stats_changed = True
                break
        
        if stats_changed:
            print(f"Stats changed: {current_stats} -> {stats}")
            # Обновляем статистику с новым временем
            data["stats"] = {
                **stats,
                "last_update": current_time.isoformat()
            }
        else:
            print("Stats unchanged, keeping existing timestamp")
            # Статистика не изменилась, сохраняем старое время обновления
            data["stats"] = {
                **stats,
                "last_update": current_stats.get("last_update", current_time.isoformat())
            }
        
        # Обновляем время последнего обновления сообщения
        if data["stats_message"].get("message_id"):
            data["stats_message"]["last_updated"] = current_time.isoformat()
        
        self._save_data(data)
    
    def get_stats(self) -> Dict[str, int]:
        """Получает текущую статистику тикетов"""
        data = self._load_data()
        return data.get("stats", {})
    
    def clear_message_info(self) -> None:
        """Очищает информацию о сообщении (когда нужно создать новое)"""
        data = self._load_data()
        data["stats_message"] = {
            "chat_id": None,
            "message_id": None,
            "created_at": None,
            "last_updated": None
        }
        self._save_data(data)
    
    def format_stats_message(self, stats: Dict[str, Any]) -> str:
        """Форматирует статистику в текст сообщения в новом формате"""
        # Используем время последнего обновления статистики из данных
        data = self._load_data()
        last_update = data.get("detailed_stats", {}).get("last_update")
        
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update)
                date_str = update_time.strftime('%d.%m.%Y')
                time_str = update_time.strftime('%d.%m.%Y %H:%M')
            except:
                current_time = now()
                date_str = current_time.strftime('%d.%m.%Y')
                time_str = current_time.strftime('%d.%m.%Y %H:%M')
        else:
            current_time = now()
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%d.%m.%Y %H:%M')
        
        # Получаем данные
        new_count = stats.get('new_count', 0)
        in_progress_count = stats.get('in_progress_count', 0)
        new_tickets = stats.get('new_tickets', [])
        in_progress_tickets = stats.get('in_progress_tickets', [])
        
        # Формируем строки с номерами заявок
        new_tickets_str = ', '.join(f"{str(ticket)}" for ticket in new_tickets) if new_tickets else "нет"
        in_progress_tickets_str = ', '.join(f"{str(ticket)}" for ticket in in_progress_tickets) if in_progress_tickets else "нет"
        
        # Формируем сообщение в новом формате
        message = "<b>📊 Статистика заявок</b>\n\n"
        message += f"<b>Непринятых заявок:</b>\n{new_count}\n"
        message += f"<b>Заявок в работе:</b>\n{in_progress_count}\n"
        message += f"<b>Непринятые заявки:</b>\n{new_tickets_str}\n"
        message += f"<b>Заявки в работе:</b>\n{in_progress_tickets_str}"
        message += f"\n\n<b>Время обновления:</b> {time_str}"
        
        return message
    
    def _setup_event_handlers(self):
        """Настройка обработчиков событий для автоматического обновления статистики"""
        # Подписываемся на события изменения статистики
        self.bot.managers.event.on('ticket_stats_changed', self._handle_stats_changed)
    
    def start_periodic_check(self):
        """Запускает задачу периодической проверки сообщения"""
        asyncio.create_task(self._periodic_message_check())
    
    async def _handle_stats_changed(self):
        """Обработчик события изменения статистики тикетов"""
        try:
            print("=== STATS CHANGED EVENT TRIGGERED ===")
            
            # Получаем детальную статистику
            stats = await self.bot.services.tickets.get_detailed_tickets_statistics()
            print(f"Current detailed stats: {stats}")
            
            # Обновляем статистику в менеджере
            self.update_detailed_stats(stats)
            
            # Обновляем сообщение
            await self._update_stats_message()
            
            print("=== STATS CHANGED EVENT COMPLETED ===")
            
        except Exception as e:
            print(f"Error handling stats change: {e}")
    
    def update_detailed_stats(self, stats: Dict[str, Any]) -> None:
        """Обновляет детальную статистику тикетов"""
        data = self._load_data()
        current_time = now()
        
        # Получаем текущую статистику для сравнения
        current_stats = data.get("detailed_stats", {})
        
        # Проверяем, изменилась ли статистика
        stats_changed = False
        for key in ['new_count', 'in_progress_count']:
            if current_stats.get(key, 0) != stats.get(key, 0):
                stats_changed = True
                break
        
        # Также проверяем изменения в списках ID
        if (current_stats.get('new_tickets', []) != stats.get('new_tickets', []) or
            current_stats.get('in_progress_tickets', []) != stats.get('in_progress_tickets', [])):
            stats_changed = True
        
        if stats_changed:
            print(f"Detailed stats changed: {current_stats} -> {stats}")
            # Обновляем статистику с новым временем
            data["detailed_stats"] = {
                **stats,
                "last_update": current_time.isoformat()
            }
        else:
            print("Detailed stats unchanged, keeping existing timestamp")
            # Статистика не изменилась, сохраняем старое время обновления
            data["detailed_stats"] = {
                **stats,
                "last_update": current_stats.get("last_update", current_time.isoformat())
            }
        
        # Обновляем время последнего обновления сообщения
        if data["stats_message"].get("message_id"):
            data["stats_message"]["last_updated"] = current_time.isoformat()
        
        self._save_data(data)
    
    async def _update_stats_message(self):
        """Обновляет сообщение со статистикой"""
        try:
            print("--- Starting stats message update ---")
            
            admin_chat_id = self.bot.managers.headers.get("ADMIN_CHAT_ID")
            if not admin_chat_id:
                print("Admin chat ID not configured")
                return
            
            print(f"Admin chat ID: {admin_chat_id}")
            
            # Получаем детальную статистику
            stats = await self.bot.services.tickets.get_detailed_tickets_statistics()
            
            # Форматируем сообщение
            message_text = self.format_stats_message(stats)
            
            # Получаем информацию о текущем сообщении
            message_info = self.get_message_info()
            print(f"Current message info: {message_info}")
            
            # Проверяем, истек ли срок редактирования (48 часов)
            if message_info and not self.is_message_expired():
                print("Message exists and not expired, trying to edit...")
                
                # Пытаемся отредактировать существующее сообщение
                success = await self.bot.managers.message.edit_message(
                    chat_id=message_info["chat_id"],
                    message_id=message_info["message_id"],
                    text=message_text,
                    parse_mode='HTML'
                )
                
                if success:
                    print("Stats message updated successfully via edit")
                    # Обновляем время последнего обновления
                    data = self._load_data()
                    data["stats_message"]["last_updated"] = now().isoformat()
                    self._save_data(data)
                    return
                else:
                    print("Failed to edit message, will create new one")
                    # Если не удалось отредактировать, создаем новое
                    await self._create_new_stats_message(admin_chat_id, message_text)
            else:
                # Создаем новое сообщение (срок истек или сообщение не существует)
                reason = "expired" if message_info else "not found"
                print(f"Stats message {reason}, creating new one")
                await self._create_new_stats_message(admin_chat_id, message_text)
                
            print("--- Stats message update completed ---")
                
        except Exception as e:
            print(f"Error updating stats message: {e}")
    
    async def _create_new_stats_message(self, chat_id: str, message_text: str):
        """Создает новое сообщение со статистикой"""
        try:
            # Удаляем старое сообщение только если оно существует
            old_message_deleted = await self._delete_old_message()
            
            # Отправляем новое сообщение
            message = await self.bot.application.bot.send_message(
                chat_id=int(chat_id),
                text=message_text,
                parse_mode='HTML'
            )
            
            # Закрепляем сообщение
            try:
                await self.bot.application.bot.pin_chat_message(
                    chat_id=int(chat_id),
                    message_id=message.message_id,
                    disable_notification=True
                )
                print("Stats message pinned successfully")
            except Exception as e:
                print(f"Failed to pin message: {e}")
            
            # Сохраняем информацию о новом сообщении
            self.save_message_info(int(chat_id), message.message_id)
            
            action = "replaced" if old_message_deleted else "created"
            print(f"New stats message {action}: {message.message_id}")
            
        except Exception as e:
            print(f"Error creating new stats message: {e}")
    
    async def _delete_old_message(self) -> bool:
        """
        Удаляет старое сообщение со статистикой
        
        Returns:
            True если сообщение было удалено, False если не было сообщения для удаления
        """
        try:
            message_info = self.get_message_info()
            if not message_info or not message_info.get("chat_id") or not message_info.get("message_id"):
                return False
                
            success = await self.bot.managers.message.delete_message(
                chat_id=message_info["chat_id"],
                message_id=message_info["message_id"]
            )
            
            if success:
                print("Old stats message deleted")
                # Очищаем информацию о старом сообщении
                self.clear_message_info()
                return True
            else:
                print("Failed to delete old message")
                # Все равно очищаем информацию, так как сообщение может не существовать
                self.clear_message_info()
                return False
                
        except Exception as e:
            print(f"Error deleting old message: {e}")
            return False
    
    async def _periodic_message_check(self):
        """Периодическая проверка и обновление сообщения"""
        while True:
            try:
                await asyncio.sleep(3600)  # Проверяем каждый час
                
                # Проверяем, истек ли срок редактирования
                if self.is_message_expired():
                    print("Stats message expired, creating new one")
                    await self._update_stats_message()
                    
            except Exception as e:
                print(f"Error in periodic message check: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке
    
    async def force_update_stats(self) -> bool:
        """
        Принудительное обновление статистики (для тестирования и ручного запуска)
        
        Returns:
            True если обновление прошло успешно, False в противном случае
        """
        try:
            print("Force updating stats message...")
            
            # Получаем детальную статистику
            stats = await self.bot.services.tickets.get_detailed_tickets_statistics()
            
            # Обновляем статистику в менеджере
            self.update_detailed_stats(stats)
            
            # Обновляем сообщение
            await self._update_stats_message()
            
            print("Stats force update completed")
            return True
            
        except Exception as e:
            print(f"Error in force update stats: {e}")
            return False
    
    async def recreate_stats_message(self) -> bool:
        """
        Пересоздает сообщение статистики (для команды /stats)
        Удаляет старое сообщение и создает новое, закрепляя его
        
        Returns:
            True если пересоздание прошло успешно, False в противном случае
        """
        try:
            print("Recreating stats message via /stats command...")
            
            admin_chat_id = self.bot.managers.headers.get("ADMIN_CHAT_ID")
            if not admin_chat_id:
                print("Admin chat ID not configured")
                return False
            
            # Получаем детальную статистику
            stats = await self.bot.services.tickets.get_detailed_tickets_statistics()
            
            # Обновляем статистику в менеджере
            self.update_detailed_stats(stats)
            
            # Форматируем сообщение
            message_text = self.format_stats_message(stats)
            
            # Принудительно создаем новое сообщение (удалив старое)
            await self._create_new_stats_message(admin_chat_id, message_text)
            
            print("Stats message recreated successfully")
            return True
            
        except Exception as e:
            print(f"Error recreating stats message: {e}")
            return False
    
    async def initialize_stats_message(self):
        """Инициализирует сообщение со статистикой при запуске бота"""
        try:
            admin_chat_id = self.bot.managers.headers.get("ADMIN_CHAT_ID")
            if not admin_chat_id:
                print("Admin chat ID not configured for stats")
                return
            
            # Получаем детальную статистику
            stats = await self.bot.services.tickets.get_detailed_tickets_statistics()
            self.update_detailed_stats(stats)
            
            # Проверяем существующее сообщение
            message_info = self.get_message_info()
            
            if not message_info or self.is_message_expired():
                # Создаем новое сообщение
                message_text = self.format_stats_message(stats)
                await self._create_new_stats_message(admin_chat_id, message_text)
            else:
                # Обновляем существующее
                await self._update_stats_message()
            
            # Запускаем периодическую проверку
            self.start_periodic_check()
                
            print("Stats message initialized")
            
        except Exception as e:
            print(f"Error initializing stats message: {e}") 
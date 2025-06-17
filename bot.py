import logging
import argparse
import asyncio
from constants import Dialogs, Actions, Variables
from typing import Callable, Coroutine, Any
from dyn_dialogs_callbacks.profile_callback import profile_callback
from dyn_dialogs_callbacks.poll_callback import poll_callback
from dyn_dialogs_callbacks.service_callback import service_callback
from dyn_dialogs_callbacks.feedback_callback import feedback_callback
from dyn_dialogs_callbacks.service_feedback_callback import service_feedback_callback
from dyn_dialogs_callbacks.spaces_callback import spaces_callback
from dialogs import (
    start_app_dialog,
    start_dyn_dialog,
    start_feedback_dialog,
    start_menu_dialog,
    start_profile_dialog,
    start_service_dialog,
    start_poll_dialog,
    start_service_feedback_dialog,
    start_spaces_dialog
)
from dialogs.stats_dialog import start_stats_dialog
from managers import (
    ManagerRegistry, StorageManager, HeadersManager, MessageManager, 
    EventManager, RouterManager, StatsManager, NotificationManager, ServicesManager
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database_manager import DatabaseManager
from entities.dialog import Dialog

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

class Utils:
    def __init__(self):
        self.dialog_converter = DialogConverter()
        self.locales_extractor = DictExtractor(LocalisationData)

class DynDialogHandlersManager:
    def __init__(self):
        self.handlers: dict[int, Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]]] = {}
        self.default_handler: Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]] | None = None

    def add_handler(self, key: int, handler: Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]]):
        self.handlers[key] = handler

    async def handle(self, key, bot, update: Update, context: ContextTypes.DEFAULT_TYPE, dialog: Dialog, sequence_id: int, item_id: int, option_id: int | None, answer: str | None, state: int):
        if key in self.handlers:
            await self.handlers[key](bot, update, context, dialog, sequence_id, item_id, option_id, answer, state)
        else:
            if self.default_handler:
                await self.default_handler(bot, update, context, dialog, sequence_id, item_id, option_id, answer, state)

class Bot:
    def __init__(self, application: Application, database_manager: DatabaseManager, headers_data: dict = None):
        self.database_manager = database_manager
        self.application = application
        # Инициализируем утилиты
        from utils import DictExtractor, DialogConverter
        from locales.localisation_uni import Data as LocalisationData
        
        class Utils:
            def __init__(self):
                self.dialog_converter = DialogConverter()
                self.locales_extractor = DictExtractor(LocalisationData)
        
        self.utils = Utils()
        self.dyn_dialog_handlers_manager = DynDialogHandlersManager()
        self.dyn_dialogs: dict[int, Dialog] = {}
        
        # Инициализируем систему менеджеров
        self.managers = ManagerRegistry(self)
        self._setup_managers(headers_data or {})
        
        # Получаем доступ к сервисам через ServicesManager
        self.services = self.managers.services.get_registry()
    
    def _setup_managers(self, headers_data: dict) -> None:
        """Настройка и регистрация всех менеджеров"""
        # Регистрируем менеджеры в правильном порядке (учитывая зависимости)
        self.managers.register_manager(StorageManager(self))
        self.managers.register_manager(HeadersManager(self))
        self.managers.register_manager(EventManager(self))
        self.managers.register_manager(MessageManager(self))
        self.managers.register_manager(RouterManager(self))
        self.managers.register_manager(StatsManager(self))
        self.managers.register_manager(NotificationManager(self))
        self.managers.register_manager(ServicesManager(self))
    
        if headers_data:
            self.managers.headers.update(headers_data)
    

    async def handle_error(self, code: int, message: str):
        """Простой обработчик ошибок"""
        print(f"Error {code}: {message}")

    def get_user_id(self, update: Update) -> int | None:
        if update.message and update.message.from_user:
            return update.message.from_user.id
        elif update.callback_query:
            return update.callback_query.from_user.id
        return None

    def get_text(self, key: str, payload: list[str] | None = None, group: str | None = "RU") -> str:
        text = self.utils.locales_extractor.get(key, payload, group) or key
        return text

    async def send_message(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    payload: list[str] | None = None,
    parse_mode: ParseMode = ParseMode.HTML,
    dynamic: bool = True,
    refresh = False,
    images: list[str] | None = None
    ) -> None:
        """Делегирует отправку сообщения в MessageManager"""
        await self.managers.message.send_message(
            update, context, text, reply_markup, payload, parse_mode, dynamic, refresh, images
        )

    def create_keyboard(self, rows: list[list[tuple[str, int | str]]]) -> InlineKeyboardMarkup:
        keyboard = []
        for row in rows:
            keyboard_row = []
            for item in row:
                text = self.get_text(item[0])
                callback_data = item[1]
                keyboard_row.append(InlineKeyboardButton(text, callback_data=callback_data))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(keyboard)

    def start(self):
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.SERVICE, service_callback)
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.PROFILE, profile_callback)
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.POLL, poll_callback)
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.FEEDBACK, feedback_callback)
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.SERVICE_FEEDBACK, service_feedback_callback)
        self.dyn_dialog_handlers_manager.add_handler(Dialogs.SPACES, spaces_callback)
        self.dyn_dialogs = {
            Dialogs.SERVICE: self.utils.dialog_converter.convert("./assets/service_dialog.json"),
            Dialogs.PROFILE: self.utils.dialog_converter.convert("./assets/profile_dialog.json"),
            Dialogs.POLL: self.utils.dialog_converter.convert("./assets/poll_dialog.json"),
            Dialogs.FEEDBACK: self.utils.dialog_converter.convert("./assets/feedback_dialog.json"),
            Dialogs.SERVICE_FEEDBACK: self.utils.dialog_converter.convert("./assets/service_feedback_dialog.json")
        }
        self.managers.router.add_handler(Dialogs.START, start_app_dialog)
        self.managers.router.add_handler(Dialogs.DYN_DIALOG_ITEM, start_dyn_dialog)
        self.managers.router.add_handler(Dialogs.FEEDBACK, start_feedback_dialog)
        self.managers.router.add_handler(Dialogs.MENU, start_menu_dialog)
        self.managers.router.add_handler(Dialogs.PROFILE, start_profile_dialog)
        self.managers.router.add_handler(Dialogs.SERVICE, start_service_dialog)
        self.managers.router.add_handler(Dialogs.POLL, start_poll_dialog)
        self.managers.router.add_handler(Dialogs.SERVICE_FEEDBACK, start_service_feedback_dialog)
        self.managers.router.add_handler(Dialogs.SPACES, start_spaces_dialog)
        self.managers.router.add_handler(Dialogs.STATS, start_stats_dialog)
        self.application.add_handler(CommandHandler("start", self.handle_command))
        self.application.add_handler(CommandHandler("menu", self.handle_command))
        self.application.add_handler(CommandHandler("service", self.handle_command))
        self.application.add_handler(CommandHandler("profile", self.handle_command))
        self.application.add_handler(CommandHandler("poll", self.handle_command))
        self.application.add_handler(CommandHandler("feedback", self.handle_command))
        self.application.add_handler(CommandHandler("service_feedback", self.handle_command))
        self.application.add_handler(CommandHandler("spaces", self.handle_command))
        self.application.add_handler(CommandHandler("stats", self.handle_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Устанавливаем хук для инициализации менеджеров
        self.application.post_init = self._post_init_hook
        
        self.application.run_polling()

    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            command = update.message.text[1:] 
            dialog_map = {
                "start": Dialogs.START,
                "menu": Dialogs.MENU,
                "service": Dialogs.SERVICE,
                "profile": Dialogs.PROFILE,
                "poll": Dialogs.POLL,
                "feedback": Dialogs.FEEDBACK,
                "service_feedback": Dialogs.SERVICE_FEEDBACK,
                "spaces": Dialogs.SPACES,
                "stats": Dialogs.STATS
            }
            if command in dialog_map:
                dialog_id = dialog_map[command]
                self.managers.router.remove_trace_items(context, 0, 0)
                self.managers.router.set_entry_point_item(context, dialog_id)
                await self.managers.router.execute(dialog_id, update, context)
        except Exception as e:
            print(f"Error handling command: {e}")
            await self.managers.router.execute(Dialogs.MENU, update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            callback_data = update.callback_query.data
            user_id = self.get_user_id(update)
            handler, dialog_type = self.managers.event.get_input_handler(user_id)
            if handler and dialog_type == Actions.CALLBACK:
                self.managers.event.remove_input_handler(user_id)
                self.managers.storage.set(context, Variables.HANDLED_DATA, callback_data)
                await handler(update, context)
                return
            else:
                if ":" in callback_data:
                    action, *params = callback_data.split(":")
                else:
                    action = callback_data
                    params = []
                
                if action == str(Dialogs.DYN_DIALOG_ITEM) and params and params[0] == "-1":
                    action_id = action
                else:
                    try:
                        action_id = int(action)
                    except ValueError:
                        action_id = action
                
                if params:
                    context.user_data['callback_params'] = params
                await self.managers.router.execute(action_id, update, context)
        except Exception as e:
            print(f"Error handling callback: {e}")
            await self.send_message(update, context, "Произошла ошибка при обработке запроса. Разработчик уже уведомлен о проблеме.")
            await self.managers.router.execute(Dialogs.MENU, update, context)
            raise e

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = self.get_user_id(update)
        print(f"handle_message: chat_id: {update.message.chat.id}")
        print(f"handle_message: user_id: {user_id}")
        if not user_id:
            return
        handler, dialog_type = self.managers.event.get_input_handler(user_id)
        if handler and dialog_type == Actions.TYPING:
            text = update.message.text.strip()
            self.managers.event.remove_input_handler(user_id)
            self.managers.storage.set(context, Variables.HANDLED_DATA, text)
            await handler(update, context)
        else:
            chat_id = update.message.chat.id if update.message else None
            
            # Проверяем, является ли это сообщением в админ-чате с ответом на заявку
            if chat_id and self.managers.notification.is_admin_chat(chat_id) and update.message.reply_to_message:
                await self.managers.notification.handle_admin_reply(update, context)

    def register_input_handler(self, user_id: int, dialog_type: int, handler: Callable[..., Coroutine[Any, Any, Any]]) -> None:
        self.managers.event.register_input_handler(user_id, dialog_type, handler)

    async def _post_init_hook(self, application):
        """Хук для инициализации всех менеджеров после старта бота"""
        try:
            # Инициализируем все менеджеры
            await self.managers.initialize_all()
            print("Bot post-initialization completed")
        except Exception as e:
            print(f"Error in post-initialization: {e}")

class Agent:
    def __init__(self):
        self.database_manager: DatabaseManager | None = None
        self.application: Application | None = None
        self.bot: Bot | None = None

    def start(self, token: str, db_url: str, admin_chat_id: str, chief_engineer_chat_id: str = None):
        self.database_manager = DatabaseManager(db_url)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.database_manager.initialize_db())
        self.application = Application.builder().token(token).build()
        
        # Подготавливаем данные заголовков для передачи в Bot
        headers_data = {
            "ADMIN_CHAT_ID": admin_chat_id
        }
        if chief_engineer_chat_id:
            headers_data["CHIEF_ENGINEER_CHAT_ID"] = chief_engineer_chat_id
            
        self.bot = Bot(
            self.application,
            self.database_manager,
            headers_data
        )
        self.bot.start()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telegram бот с подключением к MySQL"
    )
    parser.add_argument(
        "--token", 
        type=str, 
        required=True,
        help="Токен Telegram бота"
    )
    parser.add_argument(
        "--db-url", 
        type=str, 
        required=True,
        help="URL подключения к базе данных"
    )
    args = parser.parse_args()
    token = args.token
    db_url = args.db_url
    agent = Agent()
    agent.start(token, db_url, "", "")

if __name__ == "__main__":
    main()

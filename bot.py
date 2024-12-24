import argparse
import asyncio
import logging
from constants import Dialogs, Actions, Variables
from typing import Callable, Coroutine, Any

from dyn_dialogs_callbacks.profile_callback import profile_callback
from dyn_dialogs_callbacks.poll_callback import poll_callback
from dyn_dialogs_callbacks.service_callback import service_callback
from dyn_dialogs_callbacks.feedback_callback import feedback_callback

from dialogs import (
    start_app_dialog,
    start_dyn_dialog,
    start_dyn_dialog_typing_subdialog,
    start_dyn_dialog_select_subdialog,
    start_dyn_dialog_upload_subdialog,
    start_prev_dyn_dialog,
    start_feedback_dialog,
    start_menu_dialog,
    start_profile_dialog,
    start_service_dialog,
    start_poll_dialog
)

from dialogs.handlers.dialog_input_handlers import (
    handle_text_input,
    cancel_text_input,
    handle_image_input,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


from locales.localisation_uni import Data as LocalisationData
from database_manager import DatabaseManager
from entities.dialog import Dialog
from services import FeedbacksService, PollService, ServicesService, UsersService
from utils import DictExtractor, DialogConverter


class Utils:
    def __init__(self):
        self.dialog_converter = DialogConverter()
        self.locales_extractor = DictExtractor(LocalisationData)


class DynDialogHandlersManager:
    def __init__(self):
        self.handlers : dict[int, Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]]] = {}
        self.default_handler: Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]] | None = None

    def add_handler(self, key: int, handler: Callable[["Bot", Update, ContextTypes.DEFAULT_TYPE, Dialog, int, int, int | None, str | None, int], Coroutine[Any, Any, int | str]]):
        self.handlers[key] = handler

    async def handle(self, key, bot, update: Update, context: ContextTypes.DEFAULT_TYPE, dialog: Dialog, sequence_id: int, item_id: int, option_id: int | None, answer: str | None, state: int):
        if key in self.handlers:
            await self.handlers[key](bot, update, context, dialog, sequence_id, item_id, option_id, answer, state)
        else:
            if self.default_handler:
                await self.default_handler(bot, update, context, dialog, sequence_id, item_id, option_id, answer, state)


class Storage:
    def __inti__(self):
        pass

    def get(self, context: ContextTypes.DEFAULT_TYPE, key : int):
        if context.user_data:
            return context.user_data.get(key)
        return None

    def set(self, context: ContextTypes.DEFAULT_TYPE, key : int, value):
        if context.user_data is not None:
            context.user_data[key] = value
        return None


class Router:
    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.dialogs : dict[int, Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int | str]]] = {}
        self.handlers : dict[int, Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int | str]]] = {}
        self.map_to_parent : dict[int, int | str] = {}

    def add_dialog(self, key: int, dialog: Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int | str]]):
        self.dialogs[key] = dialog

    def add_back_route(self, key: int, parent_key: int):
        self.map_to_parent[key] = parent_key

    def add_handler(self, key: int, handler: Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int]]):
        self.handlers[key] = handler

    async def execute(self, key: int | str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | str:
        try:
            return await self._get_dialog(key)(update, context, self.bot)
        except KeyError:
            return await self._get_handler(key)(update, context, self.bot)


    def _get_dialog(self, key: int | str) -> Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int | str]]:
        if key in self.dialogs:
            return self.dialogs[key]
        else:
            raise KeyError("No dialog with this key")

    def _get_handler(self, key: int | str) -> Callable[[Update, ContextTypes.DEFAULT_TYPE, "Bot"], Coroutine[Any, Any, int | str]]:
        if key in self.handlers:
            return self.handlers[key]
        else:
            raise KeyError("No handler with this key")

    async def execute_entry_point (self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot: "Bot") -> int | str:
        entry_point = self.get_entry_point_item(context)
        if entry_point is not None:
            self.remove_trace_items(context, 0, 0)
            return await self.execute(entry_point, update, context)
        return -1

    async def execute_parent(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot: "Bot") -> int | str:
        parent = self.get_parent_item(context)
        if parent is not None:
            # self.remove_trace_items(context, 0, 1)
            return await self.execute(parent, update, context)
        return -1

    async def execute_previous(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot: "Bot") -> int | str:
        previous = self.get_previous_trace_item(context)
        current_trace = self.get_current_trace(context)
        if previous is not None:
            current_trace = current_trace[:-1]
            if len(current_trace) > 1:
                self._set_current_trace(context, current_trace)
            return await self.execute(previous, update, context)
        return -1

    def get_current_trace(self, context : ContextTypes.DEFAULT_TYPE) -> list[int | str]:
        current_trace = self.bot.local_storage.get(context, Variables.ACTIVE_DIALOG_TRACE)
        if current_trace is None:
            return []
        return current_trace

    def _set_current_trace(self, context : ContextTypes.DEFAULT_TYPE, current_trace : list[int | str]):
        self.bot.local_storage.set(context, Variables.ACTIVE_DIALOG_TRACE, current_trace.copy())

    def add_trace_item(self, context : ContextTypes.DEFAULT_TYPE, item : int | str):
        current_trace = self.get_current_trace(context)
        if current_trace is None:
            current_trace = []
        current_trace.append(item)
        self._set_current_trace(context, current_trace)

    def set_entry_point_item(self, context : ContextTypes.DEFAULT_TYPE, item : int):
        current_trace = self.get_current_trace(context)
        current_trace = []
        current_trace.insert(0, item)
        self._set_current_trace(context, current_trace)

    def set_parent_item(self, context : ContextTypes.DEFAULT_TYPE, item : int):
        current_trace = self.get_current_trace(context)
        if current_trace is None or len(current_trace) == 0:
            current_trace = [0, item]
        elif len(current_trace) >= 2:
            current_trace[1] = item
        else:
            current_trace.append(item)
        self._set_current_trace(context, current_trace)

    def remove_trace_items(self, context : ContextTypes.DEFAULT_TYPE, start: int, end: int):
        current_trace = self.get_current_trace(context)
        if current_trace is None:
            return
        current_trace = current_trace[start:end]
        self._set_current_trace(context, current_trace)

    def pop_previous_trace_item(self, context : ContextTypes.DEFAULT_TYPE) -> int | str | None:
        current_trace = self.get_current_trace(context)
        prev_trace_item = None
        if current_trace is None or len(current_trace) == 0:
            return None
        prev_trace_item = current_trace[len(current_trace)-1]
        print(current_trace)
        current_trace = current_trace[:-1]
        print(current_trace)
        self._set_current_trace(context, current_trace)
        return prev_trace_item

    def get_parent_item(self, context : ContextTypes.DEFAULT_TYPE) -> int | str | None:
        current_trace = self.get_current_trace(context)
        if current_trace is None or len(current_trace) <= 1:
            return None
        parent = current_trace[1]
        return parent

    def get_entry_point_item(self, context : ContextTypes.DEFAULT_TYPE) -> int | str | None:
        current_trace = self.get_current_trace(context)
        if current_trace is None:
            return None
        if len(current_trace) == 0:
            return None
        first_item = current_trace[0]
        return first_item

    def get_current_trace_item(self, context : ContextTypes.DEFAULT_TYPE) -> int | str | None:
        current_trace = self.get_current_trace(context)
        if current_trace is None:
            return None
        if len(current_trace) == 0:
            return None
        return current_trace[-1]


class ErrorHandler:
    def __init__(self):
        pass

    async def handle(self, code: int, message: str):
        print(message)


class Bot:

    def __init__(self, application: Application, database_manager: DatabaseManager, utils: Utils, local_storage: Storage, error_handler: ErrorHandler):
        self.database_manager = database_manager
        self.application = application
        self.error_handler = error_handler
        self.local_storage = Storage()
        self.user_service = UsersService(self.database_manager)
        self.service_service = ServicesService(self.database_manager)
        self.poll_service = PollService(self.database_manager)
        self.feedback_service = FeedbacksService(self.database_manager)
        self.utils = utils
        self.router = Router(self)
        self.local_storage = local_storage
        self.dyn_dialog_handlers_manager: DynDialogHandlersManager = DynDialogHandlersManager()
        self.dyn_dialogs : dict[int, Dialog] = {}


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
    refresh = False
) -> None:
        text = self.get_text(text, payload, 'RU')
        if not dynamic or refresh:
            chat_id = None
            if update.message:
                chat_id = update.message.chat.id
            elif update.callback_query and update.callback_query.message:
                chat_id = update.callback_query.message.chat.id

            if chat_id:
                try:
                    if refresh:
                        buffer_message = self.local_storage.get(context, Variables.BUFFER_MESSAGE)
                        if buffer_message:
                            try:
                                await context.bot.delete_message(
                                    chat_id=buffer_message.chat_id, message_id=buffer_message.message_id
                                )
                            except Exception as e:
                                await self.error_handler.handle(1000, str(e))
                            self.local_storage.set(context, Variables.BUFFER_MESSAGE, None)

                    message = await context.bot.send_message(
                        chat_id,
                        text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                    )

                    if message and dynamic:
                        self.local_storage.set(context, Variables.BUFFER_MESSAGE, message)
                except Exception as e:
                    await self.error_handler.handle(1001, str(e))

        elif update.callback_query:
            try:
                message = await update.callback_query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                self.local_storage.set(context, Variables.BUFFER_MESSAGE, message)
            except Exception as e:
                await self.error_handler.handle(1002, str(e))

        elif update.message:
            try:
                buffer_message = self.local_storage.get(context, Variables.BUFFER_MESSAGE)
                if buffer_message:
                    try:
                        await context.bot.delete_message(
                            chat_id=buffer_message.chat_id, message_id=buffer_message.message_id
                        )
                    except Exception as e:
                        await self.error_handler.handle(1000, str(e))
                    self.local_storage.set(context, Variables.BUFFER_MESSAGE, None)

                message = await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
                self.local_storage.set(context, Variables.BUFFER_MESSAGE, message)
            except Exception as e:
                await self.error_handler.handle(1003, str(e))


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
        self.dyn_dialogs = {
            Dialogs.SERVICE: self.utils.dialog_converter.convert("./assets/service_dialog.json"),
            Dialogs.PROFILE: self.utils.dialog_converter.convert("./assets/profile_dialog.json"),
            Dialogs.POLL: self.utils.dialog_converter.convert("./assets/poll_dialog.json"),
            Dialogs.FEEDBACK: self.utils.dialog_converter.convert("./assets/feedback_dialog.json")
        }
        self.router.add_dialog(Dialogs.START, start_app_dialog)
        self.router.add_dialog(Dialogs.DYN_DIALOG_ITEM, start_dyn_dialog)
        self.router.add_dialog(Dialogs.DYN_DIALOG_TEXT_INPUT, start_dyn_dialog_typing_subdialog)
        self.router.add_dialog(Dialogs.DYN_DIALOG_OPTION_SELECT, start_dyn_dialog_select_subdialog)
        self.router.add_dialog(Dialogs.DYN_DIALOG_IMAGE_UPLOAD, start_dyn_dialog_upload_subdialog)
        self.router.add_dialog(Dialogs.DYN_DIALOG_PREV_ITEM, start_prev_dyn_dialog)
        self.router.add_dialog(Dialogs.FEEDBACK, start_feedback_dialog)
        self.router.add_dialog(Dialogs.MENU, start_menu_dialog)
        self.router.add_dialog(Dialogs.PROFILE, start_profile_dialog)
        self.router.add_dialog(Dialogs.SERVICE, start_service_dialog)
        self.router.add_dialog(Dialogs.POLL, start_poll_dialog)

        self.router.add_handler(Actions.TYPING, handle_text_input)
        self.router.add_handler(Actions.CANCELING, cancel_text_input)
        self.router.add_handler(Actions.UPLOADING, handle_image_input)

        service_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.SERVICE,update, context),
                    pattern="^" + str(Dialogs.SERVICE) + "$"
                )
            ],
            states={
                Actions.TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.TYPING,update, context))],
                Actions.UPLOADING: [
                    MessageHandler(filters.PHOTO & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.UPLOADING ,update, context))
                ],
                Dialogs.DYN_DIALOG_OPTION_SELECT: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_TEXT_INPUT : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_IMAGE_UPLOAD : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_ITEM: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Actions.CANCELING) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_PREV_ITEM, update, context),
                    pattern="^" + str(Actions.BACK) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.MENU,update, context),
                    pattern="^" + str(Dialogs.MENU) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.SERVICE, update, context),
                    pattern="^" + str(Dialogs.SERVICE) + r":?(\d+)?$")
            ],
            map_to_parent={Dialogs.MENU: Dialogs.MENU},
        )

        profile_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.PROFILE,update, context),
                    pattern="^" + str(Dialogs.PROFILE) + "$"
                )
            ],
            states={
                Actions.TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.TYPING,update, context))],
                Actions.UPLOADING: [
                    MessageHandler(filters.PHOTO & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.UPLOADING ,update, context))
                ],
                Dialogs.DYN_DIALOG_OPTION_SELECT: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_TEXT_INPUT : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_IMAGE_UPLOAD : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_ITEM: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Actions.CANCELING) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.MENU,update, context),
                    pattern="^" + str(Dialogs.MENU) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.PROFILE, update, context),
                    pattern="^" + str(Dialogs.PROFILE) + r":?(\d+)?$",
                )
            ],
            map_to_parent={Dialogs.MENU: Dialogs.MENU},
        )

        polling_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.POLL,update, context),
                    pattern="^" + str(Dialogs.POLL) + "$"
                )
            ],
            states={
                Actions.TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.TYPING,update, context))],
                Actions.UPLOADING: [
                    MessageHandler(filters.PHOTO & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.UPLOADING ,update, context))
                ],
                Dialogs.DYN_DIALOG_OPTION_SELECT: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_TEXT_INPUT : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_IMAGE_UPLOAD : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_ITEM: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Actions.CANCELING) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.MENU,update, context),
                    pattern="^" + str(Dialogs.MENU) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.POLL, update, context),
                    pattern="^" + str(Dialogs.POLL) + r":?(\d+)?$",
                )
            ],
            map_to_parent={Dialogs.MENU: Dialogs.MENU},
        )

        feedback_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.FEEDBACK,update, context),
                    pattern="^" + str(Dialogs.FEEDBACK) + "$"
                )
            ],
            states={
                Actions.TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.TYPING,update, context))],
                Actions.UPLOADING: [
                    MessageHandler(filters.PHOTO & ~filters.COMMAND, lambda update, context: self.router.execute(Actions.UPLOADING ,update, context))
                ],
                Dialogs.DYN_DIALOG_OPTION_SELECT: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_TEXT_INPUT : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_IMAGE_UPLOAD : [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$",
                    )
                ],
                Dialogs.DYN_DIALOG_ITEM: [
                    CallbackQueryHandler(
                        lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                        pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_OPTION_SELECT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_OPTION_SELECT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_TEXT_INPUT,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_TEXT_INPUT) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_IMAGE_UPLOAD,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_IMAGE_UPLOAD) + "$"
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Actions.CANCELING) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.MENU,update, context),
                    pattern="^" + str(Dialogs.MENU) + "$"),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.DYN_DIALOG_ITEM,update, context),
                    pattern="^" + str(Dialogs.DYN_DIALOG_ITEM) + r":?(\d+)?$",
                ),
                CallbackQueryHandler(
                    lambda update, context: self.router.execute(Dialogs.FEEDBACK, update, context),
                    pattern="^" + str(Dialogs.FEEDBACK) + r":?(\d+)?$",
                )
            ],
            map_to_parent={Dialogs.MENU: Dialogs.MENU},
        )

        main_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(lambda update, context: self.router.execute(Dialogs.MENU,update, context), pattern="^" + str(Dialogs.MENU) + "$"),
                CommandHandler("menu", lambda update, context: self.router.execute(Dialogs.MENU,update, context)),
            ],
            states={
                Dialogs.MENU: [
                    service_conv_handler,
                    profile_conv_handler,
                    polling_conv_handler,
                    feedback_conv_handler,
                ]
            },
            fallbacks=[
                CallbackQueryHandler(lambda update, context: self.router.execute(Dialogs.MENU,update, context), pattern="^" + str(Dialogs.MENU) + "$")
            ],
        )
        self.application.add_handler(main_conv_handler)
        self.application.add_handler(CommandHandler("start", lambda update, context: self.router.execute(Dialogs.START,update, context)))
        self.application.add_handler(CommandHandler("menu", lambda update, context: self.router.execute(Dialogs.MENU,update, context)))
        self.application.run_polling()


class Agent:
    def __init__(self):
        self.database_manager: DatabaseManager | None = None
        self.local_storage: Storage | None = None
        self.application: Application | None = None
        self.bot: Bot | None = None
        self.error_handler : ErrorHandler = ErrorHandler()
        self.utils = Utils()

    def start(self, token: str, db_url: str):
        self.database_manager = DatabaseManager(db_url)
        loop = asyncio.get_event_loop()
        self.database_manager.create_tables()
        self.local_storage = Storage()
        self.application = Application.builder().token(token).build()

        self.bot = Bot(
            self.application,
            self.database_manager,
            self.utils,
            self.local_storage,
            self.error_handler
        )
        self.bot.start()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
locales = "./locales/localisation_uni.py"


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
    agent.start(token, db_url)


if __name__ == "__main__":
    main()

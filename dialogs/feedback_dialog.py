from typing import TYPE_CHECKING
from datetime import datetime
from constants import Dialogs, Actions, Variables
from models import Feedback

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot



async def start_feedback_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:

    bot.router.set_parent_item(context, Dialogs.FEEDBACK)

    buffer = bot.local_storage.get(context, Variables.FEEDBACK_BUFFER) or "---"
    handled_data = bot.local_storage.get(context, Variables.HANDLED_DATA)
    if handled_data:
        buffer = handled_data
        bot.local_storage.set(context, Variables.FEEDBACK_BUFFER, buffer)
        bot.local_storage.set(context, Variables.HANDLED_DATA, None)

    await bot.send_message(
        update,
        context,
        "feedback_header",
        bot.create_keyboard(
            [
                [
                    ("edit_feedback", Dialogs.FEEDBACK_SET),
                    ("send", Dialogs.FEEDBACK_SEND),
                    ("back", Actions.CANCELING),
                ]
            ]
        ),
        payload=[buffer],
    )
    return Actions.SETTING


async def start_set_feedback_subdialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    keyboard = bot.create_keyboard([[("cancel", Actions.CANCELING)]])
    await bot.send_message(update, context, "feedback_text_handler_prompt", keyboard)
    return Actions.TYPING


async def start_send_feedback_subdialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    buffer = bot.local_storage.get(context, Variables.FEEDBACK_BUFFER)
    text = None
    if (
        bot.local_storage.get(context, Variables.USER_NAME) is None
        or bot.local_storage.get(context, Variables.USER_LEGAL_ENTITY) is None
        or bot.local_storage.get(context, Variables.USER_OBJECT) is None
    ):
        text = "user_profile_validation_error"
    user_id = bot.get_user_id(update)

    if user_id is None:
        return Actions.END

    elif buffer:
        await bot.feedback_service.create_feedback(
            Feedback(
                0,
                user_id= user_id,
                text=buffer,
                created_at=datetime.now(),
            )
        )
        text = "feedback_completed"
        bot.local_storage.set(context, Variables.FEEDBACK_BUFFER, None)
    else:
        text = "feedback_data_error"
    await bot.send_message(update, context, text, bot.create_keyboard([[("exit", Dialogs.MENU)]]))
    return Dialogs.FEEDBACK

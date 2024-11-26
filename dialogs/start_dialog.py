from typing import TYPE_CHECKING
from models import User
from constants import Dialogs, Actions, Variables, Roles

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_app_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot"):

    if update.message is None:
        return Actions.END
    if update.message.from_user is None:
        return Actions.END
    if update.message.from_user.username is None:
        return Actions.END

    payload = context.args[0] if context.args else None
    user_id = update.message.from_user.id
    user = await bot.user_service.get_user(user_id)
    first_start = bot.local_storage.get(context, Variables.FIRST_START)
    if user is None:
        bot.local_storage.set(context, Variables.FIRST_START, True)
        first_start = True
        user = User(user_id, update.message.from_user.username, None)
        user.object = "Норд Сити"
        user = await bot.user_service.create_user(user)
    else:
        bot.local_storage.set(context, Variables.FIRST_START, False)
        first_start = False
    if first_start:
        if payload == str(Roles.LPR):
            user.role = Roles.LPR
            await bot.send_message(update, context, "profile_identification_completed", dynamic=False)
        elif payload == str(Roles.MA):
            user.role = Roles.MA
            await bot.send_message(update, context, "profile_identification_completed", dynamic=False)
        else:
            await bot.send_message(update, context, "user_profile_identification_error", dynamic=False)
        await bot.user_service.update_user(user)
        await bot.send_message(
            update,
            context,
            "user_agreement_input_handler_prompt",
            bot.create_keyboard([[("agree", Dialogs.MENU)]])
        )
        return Dialogs.MENU
    else:
        await bot.send_message(
            update,
            context,
            "data_sync_completed",
            bot.create_keyboard([[("continue", Dialogs.MENU)]])
        )
        return Dialogs.MENU
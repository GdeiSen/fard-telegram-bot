from typing import TYPE_CHECKING
from entities.user import User
from constants import Dialogs, Actions, Variables, Roles

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot

async def start_app_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot"):
    try:
        payload = context.args[0] if context.args else None
        user_id = update.message.from_user.id
        user = await bot.user_service.get_user(user_id)
        first_start = True
        bot.local_storage.set(context, Variables.FIRST_START, True)
        if user is None:
            user = User(user_id, update.message.from_user.username, None)
            user.object = "Норд Сити"
            user = await bot.user_service.create_user(user)
        else:
            bot.local_storage.set(context, Variables.FIRST_START, False)
            first_start = False
        if user is None:
            user = User(user_id, update.message.from_user.username, None)
            user.object = "Норд Сити"
            if payload == str(Roles.LPR):
                user.role = Roles.LPR
                await bot.send_message(update, context, "profile_identification_completed", dynamic=False)
            elif payload == str(Roles.MA):
                user.role = Roles.MA
                await bot.send_message(update, context, "profile_identification_completed", dynamic=False)
            else:
                user.role = Roles.MA
            user = await bot.user_service.create_user(user)
            await bot.send_message(
                update,
                context,
                "user_agreement_input_handler_prompt",
                bot.create_keyboard([[("agree", Dialogs.MENU)]])
            )
            return Dialogs.MENU
        else:
            if payload is not None:
                if payload == str(Roles.MA):
                    user.role = Roles.MA
                elif payload == str(Roles.LPR):
                    user.role = Roles.LPR
                await bot.user_service.update_user(user)
                await bot.send_message(update, context, "profile_identification_completed", dynamic=False)
            await bot.send_message(
                update,
                context,
                "data_sync_completed",
                bot.create_keyboard([[("continue", Dialogs.MENU)]])
            )
            return Dialogs.MENU
    except Exception as e:
        print(f"Error in start_app_dialog: {e}")
        return Actions.END
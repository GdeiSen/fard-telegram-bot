from typing import TYPE_CHECKING
from constants import Dialogs, Actions, Roles

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_menu_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    bot.router.set_entry_point_item(context, Dialogs.MENU)
    user_id = bot.get_user_id(update)

    if user_id is None:
        return Actions.END

    user = await bot.user_service.get_user(user_id)

    if user is None:
        return Actions.END

    keyboard = bot.create_keyboard(
        [
            [
                ("profile", Dialogs.PROFILE),
                ("service", Dialogs.SERVICE)],
            [
                ("polling", Dialogs.POLL),
                ("feedback", Dialogs.FEEDBACK),
            ]
        ]
    )

    text = "default_greeting"

    if user.role == Roles.MA:
        text = "ma_greeting"
        keyboard = bot.create_keyboard(
            [
                [
                    ("profile",Dialogs.PROFILE),
                    ("service", Dialogs.SERVICE),
                ]
            ]
        )

    if not user.last_name or not user.first_name or not user.middle_name or not user.legal_entity:
        text = "new_greeting"
        keyboard = bot.create_keyboard(
            [
                [
                    ("login", Dialogs.PROFILE)
                ]
            ]
        )

    await bot.send_message(update, context, text, keyboard, refresh = True)
    return Dialogs.MENU

from typing import TYPE_CHECKING
from constants import Dialogs, Actions, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_profile_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    bot.router.set_entry_point_item(context, Dialogs.PROFILE)

    user_id = bot.get_user_id(update)

    if user_id is None:
        return Actions.END

    user = await bot.user_service.get_user(user_id)

    if user is None:
        return Actions.END

    last_name = user.last_name or ""
    first_name = user.first_name or ""
    middle_name = user.middle_name or ""

    user_name = last_name + " " + first_name + " " + middle_name
    user_name = user_name.replace("  ", " ")
    user_name = user_name.strip()
    user_legal_entity = user.legal_entity or ""
    user_object = user.object or ""

    bot.local_storage.set(context, Variables.USER_NAME, user_name)
    bot.local_storage.set(context, Variables.USER_OBJECT, user.object)
    bot.local_storage.set(context, Variables.USER_LEGAL_ENTITY, user.legal_entity)

    bot.local_storage.set(context, Variables.ACTIVE_DYN_DIALOG, bot.dyn_dialogs[Dialogs.PROFILE])
    bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, 0)
    bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)

    await bot.send_message(
        update,
        context,
        "profile_header",
        bot.create_keyboard(
            [
                [("login_repeat", Dialogs.DYN_DIALOG_ITEM)],
                [("back", Dialogs.MENU)],
            ]
        ),
        payload=[user_name, user_legal_entity, user_object],
        refresh=True
    )
    return Dialogs.PROFILE

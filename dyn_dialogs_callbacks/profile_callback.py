from typing import TYPE_CHECKING
from constants import Dialogs, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot
    from entities.dialog import Dialog

from constants import Variables

def is_valid_name(name: str) -> bool:
    return name.isalpha() and len(name) < 30 and " " not in name

async def profile_callback(
    bot: "Bot",
    update: "Update",
    context: "ContextTypes.DEFAULT_TYPE",
    dialog: "Dialog",
    sequence_id: "int",
    item_id: "int",
    option_id: "int | None",
    answer: "str | None",
    state: "int",
) -> int | str:

    user_id = bot.get_user_id(update)

    if user_id:
        user = await bot.user_service.get_user(user_id)

        if user:
            if item_id in {0, 1, 2}:
                if not is_valid_name(answer or ""):
                    bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, item_id)
                    await bot.send_message(
                        update,
                        context,
                        "❌ <b>Некорректный ввод.</b>\nИмена должны состоять из одного слова, содержать только буквы и быть длиной менее 30 символов.",
                        dynamic=False
                    )
                    return Dialogs.DYN_DIALOG_ITEM

                if item_id == 0:
                    user.first_name = answer
                elif item_id == 1:
                    user.last_name = answer
                elif item_id == 2:
                    user.middle_name = answer
            elif item_id == 3:
                user.legal_entity = answer

            await bot.user_service.update_user(user)

            bot.local_storage.set(context, Variables.USER_NAME, (
                (user.last_name or "") + " " +
                (user.first_name or "") + " " +
                (user.middle_name or "")
            ).strip())
            bot.local_storage.set(context, Variables.USER_LEGAL_ENTITY, user.legal_entity)

    if state == 1:
        await bot.send_message(update, context, "profile_completed", dynamic=False)
        return await bot.router.execute(Dialogs.MENU, update, context)

    return Dialogs.DYN_DIALOG_ITEM

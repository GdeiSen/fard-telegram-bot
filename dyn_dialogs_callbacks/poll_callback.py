from typing import TYPE_CHECKING
from datetime import datetime
from entities.dialog_answer import Answer
from constants import Dialogs, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot
    from entities.dialog import Dialog


async def poll_callback(
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
        user = await bot.services.users.get_user(user_id)
        if user:
            # Для опций используем ID опции как значение ответа, если answer не предоставлен
            answer_value = answer
            if answer_value is None and option_id is not None:
                answer_value = str(option_id)
            elif answer_value is None:
                answer_value = ""  # Пустая строка вместо None
                
            answer_obj = Answer(
                id = 0,
                user_id = user_id,
                dialog_id = dialog.id,
                sequence_id = sequence_id,
                item_id = item_id,
                answer = answer_value
            )
            await bot.services.polls.update_answer(user, answer_obj)
    if state == 1:
        await bot.send_message(update, context, "poll_completed", dynamic=False)
        # Очистим трейс перед переходом в меню, чтобы избежать ошибок доступа к элементам
        bot.managers.storage.set(context, Variables.ACTIVE_DIALOG_TRACE, [])
        return await bot.managers.router.execute(Dialogs.MENU, update, context)

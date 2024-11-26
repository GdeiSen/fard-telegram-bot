from typing import TYPE_CHECKING
from datetime import datetime
from models import Answer
from constants import Dialogs

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot
    from models import Dialog


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
        user = await bot.user_service.get_user(user_id)
        if user:
            answer_obj = Answer(
                id = 0,
                user_id = user_id,
                dialog_id = dialog.id,
                sequence_id = sequence_id,
                item_id = item_id,
                answer = answer or "-",
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            await bot.poll_service.update_answer(user, answer_obj)
    if state == 1:
        await bot.send_message(update, context, "poll_completed", dynamic=False)
        return await bot.router.execute(Dialogs.MENU, update, context)
    return True

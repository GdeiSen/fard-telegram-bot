from typing import TYPE_CHECKING
from datetime import datetime
from entities.dialog_answer import Answer
from entities.feedback import Feedback
from constants import Dialogs

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot
    from entities.dialog import Dialog

async def feedback_callback(
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
            feedback = Feedback(
                id=0,
                user_id=user_id,
                answer=answer,
                dialog_id=dialog.id,
                sequence_id=sequence_id,
                item_id=item_id
            )
            await bot.feedback_service.create_feedback(feedback)
    if state == 1:
        await bot.send_message(update, context, "feedback_completed", dynamic=False)
        return await bot.router.execute(Dialogs.MENU, update, context)
    return True

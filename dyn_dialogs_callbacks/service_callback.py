from typing import TYPE_CHECKING
from constants import Dialogs

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from models import Dialog
    from bot import Bot

async def service_callback(
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
    if state == 1:
        await bot.send_message(update, context, "service_ticket_completed", dynamic=False)
        return await bot.router.execute(Dialogs.MENU, update, context)

    return Dialogs.DYN_DIALOG_ITEM

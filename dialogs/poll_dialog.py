from typing import TYPE_CHECKING
from constants import Dialogs, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_poll_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    bot.router.set_entry_point_item(context, Dialogs.POLL)
    bot.local_storage.set(context, Variables.ACTIVE_DYN_DIALOG, bot.dyn_dialogs[Dialogs.POLL])
    bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, 0)
    bot.local_storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)

    await bot.send_message(
        update,
        context,
        "poll_header",
        bot.create_keyboard(
            [[("start", Dialogs.DYN_DIALOG_ITEM), ("back", Dialogs.MENU)]]
        ),
    )

    return Dialogs.FEEDBACK

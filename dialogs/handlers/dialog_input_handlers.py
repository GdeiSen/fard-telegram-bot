from typing import TYPE_CHECKING
from constants import Actions, Variables

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def handle_text_input(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    if update.message is None:
        return Actions.END
    if update.message.text is None:
        return Actions.END
    text = update.message.text.strip()
    bot.local_storage.set(context, Variables.HANDLED_DATA, text)
    return await bot.router.execute_parent(update, context, bot)


async def cancel_text_input(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    if update.message is None:
        return Actions.END
    if update.message.text is None:
        return Actions.END

    await bot.send_message(update, context, "Canceled")
    return await bot.router.execute_parent(update, context, bot)


async def handle_image_input(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    if update.message is None:
        return Actions.END
    if update.message.text is None:
        return Actions.END

    photo_file = await update.message.photo[-1].get_file()
    print(f"Image received and stored with file_id: {photo_file.file_id}")
    bot.local_storage.set(context, Variables.HANDLED_DATA, photo_file.file_id)
    return await bot.router.execute_parent(update, context, bot)
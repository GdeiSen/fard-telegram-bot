from typing import TYPE_CHECKING
from constants import Dialogs, Variables
from services.spaces_service import SpacesService
from utils.spaces_dialog_generator import SpacesDialogGenerator

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_spaces_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    """
    Диалог для просмотра свободных помещений в объектах недвижимости.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст обработчика
        bot: Экземпляр бота
    
    Returns:
        int: ID диалога
    """
    if update.effective_chat.type != "private":
        return
    
    bot.managers.router.set_entry_point_item(context, Dialogs.MENU)
    spaces_service = SpacesService(bot.database_manager)
    dialog_generator = SpacesDialogGenerator(spaces_service)
    dialog = await dialog_generator.generate_dialog(only_available=True)
    
    if dialog:
        bot.dyn_dialogs[Dialogs.SPACES] = dialog
        bot.managers.storage.set(context, Variables.ACTIVE_DYN_DIALOG, dialog)
        bot.managers.storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ID, 0)
        bot.managers.storage.set(context, Variables.ACTIVE_DIALOG_SEQUENCE_ITEM_INDEX, 0)
        return await bot.managers.router.execute(Dialogs.DYN_DIALOG_ITEM, update, context)
    else:
        await bot.send_message(
            update,
            context,
            "spaces_error_message",
            bot.create_keyboard(
                [
                    [("back", Dialogs.MENU)],
                ]
            ),
        )
    
    return Dialogs.SPACES 
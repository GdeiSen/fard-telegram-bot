from typing import TYPE_CHECKING
from constants import Dialogs, Actions

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from bot import Bot


async def start_stats_dialog(update: "Update", context: "ContextTypes.DEFAULT_TYPE", bot: "Bot") -> int:
    """Обработчик диалога статистики (для тестирования и ручного запуска)"""
    try:
        user_id = bot.get_user_id(update)
        if not user_id:
            return Actions.END
        
        # Получаем пользователя для проверки прав
        user = await bot.services.users.get_user(user_id)
        if not user:
            return Actions.END
        
        # Проверяем права администратора (можно настроить по необходимости)
        # if user.role != Roles.ADMIN:
        #     await bot.send_message(update, context, "access_denied")
        #     return Actions.END


        # Пересоздаем сообщение в админ-чате (удаляем старое, создаем новое, закрепляем)
        await bot.managers.stats.recreate_stats_message()
        
        return Dialogs.MENU
        
    except Exception as e:
        print(f"Error in start_stats_dialog: {e}")
        return Actions.END

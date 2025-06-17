from datetime import datetime, timezone, timedelta
from typing import Optional

# Конфигурация часового пояса - изменяйте здесь для смены часового пояса всей системы
# Московский часовой пояс (UTC+3)
SYSTEM_TIMEZONE = timezone(timedelta(hours=3))

class TimeUtils:
    """Централизованная утилита для работы с временем в системном часовом поясе"""
    
    @staticmethod
    def now() -> datetime:
        """Возвращает текущее время в системном часовом поясе"""
        return datetime.now(SYSTEM_TIMEZONE)
    
    @staticmethod
    def utcnow() -> datetime:
        """Возвращает текущее время в UTC"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def get_system_timezone() -> timezone:
        """Возвращает объект системного часового пояса"""
        return SYSTEM_TIMEZONE
    
    @staticmethod
    def to_system_time(dt: datetime) -> datetime:
        """Конвертирует datetime в системное время"""
        if dt.tzinfo is None:
            # Если время без часового пояса, считаем его UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(SYSTEM_TIMEZONE)
    
    @staticmethod
    def format_time(dt: Optional[datetime] = None, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """Форматирует время в системном часовом поясе"""
        if dt is None:
            dt = TimeUtils.now()
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        system_time = dt.astimezone(SYSTEM_TIMEZONE)
        return system_time.strftime(format_str)

# Глобальные функции для удобства использования
def now() -> datetime:
    """Возвращает текущее время в системном часовом поясе"""
    return TimeUtils.now()

def utcnow() -> datetime:
    """Возвращает текущее время в UTC"""
    return TimeUtils.utcnow()

# Для использования в моделях SQLAlchemy
def now_for_db():
    """Функция для использования в default параметрах SQLAlchemy моделей"""
    return TimeUtils.now()

def utc_now_for_db():
    """Функция для использования в default параметрах SQLAlchemy моделей (UTC)"""
    return TimeUtils.utcnow() 
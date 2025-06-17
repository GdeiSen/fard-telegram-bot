#!/usr/bin/env python3
"""
Скрипт для добавления записей о завершении всех невыполненных заявок
Добавляет статус 3 (выполнено) для всех тикетов со статусами 0, 1, 2
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database_manager import DatabaseManager
from models import ServiceTicket, ServiceTicketStatus
from utils.time_utils import now


async def add_completion_status_for_pending_tickets():
    """
    Добавляет записи о завершении для всех невыполненных тикетов
    """
    # Параметры
    ADMIN_ID = 1  # ID администратора (замените на нужный)
    COMPLETION_STATUS = 3  # Статус "выполнено"
    
    db_manager = DatabaseManager()
    
    try:
        async with db_manager.Session() as session:
            # Находим все невыполненные тикеты
            result = await session.execute(
                select(ServiceTicket).filter(ServiceTicket.status.in_([0, 1, 2]))
            )
            pending_tickets = result.scalars().all()
            
            if not pending_tickets:
                print("✅ Нет невыполненных тикетов для обработки")
                return
            
            print(f"📋 Найдено {len(pending_tickets)} невыполненных тикетов")
            
            current_time = now()
            added_statuses = []
            
            # Добавляем записи о завершении для каждого тикета
            for ticket in pending_tickets:
                # Создаем новую запись статуса "выполнено"
                new_status = ServiceTicketStatus(
                    id=None,
                    ticket_id=ticket.id,
                    status_type=COMPLETION_STATUS,
                    admin_id=ADMIN_ID,
                    message_id=None,
                    assignee=None,
                    created_at=current_time
                )
                
                session.add(new_status)
                added_statuses.append({
                    'ticket_id': ticket.id,
                    'current_status': ticket.status,
                    'added_completion_status': COMPLETION_STATUS
                })
                
                print(f"  Тикет #{ticket.id}: добавлена запись о завершении (статус тикета: {ticket.status})")
            
            # Сохраняем изменения
            await session.commit()
            
            print(f"\n✅ Успешно обработано {len(added_statuses)} тикетов")
            print("📊 Статистика обработки:")
            
            # Группируем по текущим статусам для статистики
            status_stats = {}
            for item in added_statuses:
                current_status = item['current_status']
                status_stats[current_status] = status_stats.get(current_status, 0) + 1
            
            status_names = {0: "Новые", 1: "Принятые", 2: "Переданные"}
            for status, count in status_stats.items():
                status_name = status_names.get(status, f"Статус {status}")
                print(f"  Тикеты со статусом '{status_name}': {count} записей о завершении")
            
    except Exception as e:
        print(f"❌ Ошибка при обработке тикетов: {e}")
        raise
    
    finally:
        await db_manager.close()


async def main():
    """Основная функция запуска скрипта"""
    print("🚀 Запуск скрипта завершения тикетов...")
    print("=" * 50)
    
    try:
        await add_completion_status_for_pending_tickets()
        print("=" * 50)
        print("🎉 Скрипт выполнен успешно!")
        
    except Exception as e:
        print("=" * 50)
        print(f"💥 Критическая ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Запускаем скрипт
    exit_code = asyncio.run(main())
    exit(exit_code) 
-- SQL скрипт для добавления записей о завершении всех невыполненных заявок
-- Добавляет статус 3 (выполнено) для всех тикетов со статусами 0, 1, 2

-- Показать текущую статистику перед обновлением
SELECT 
    'Статистика ДО обновления' as info,
    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as new_tickets,
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as accepted_tickets,
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as assigned_tickets,
    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) as completed_tickets,
    COUNT(*) as total_tickets
FROM service_ticket;

-- Добавить записи о завершении в таблицу статусов
INSERT INTO service_ticket_statuses (ticket_id, status_type, admin_id, created_at)
SELECT 
    id as ticket_id,
    3 as status_type,        -- Статус "выполнено"
    1 as admin_id,           -- ID администратора (замените на нужный)
    NOW() as created_at
FROM service_ticket 
WHERE status IN (0, 1, 2);   -- Только невыполненные тикеты

-- Основной статус тикета НЕ изменяется, 
-- так как он не связан с выполнением заявки

-- Показать статистику тикетов (статусы не изменились)
SELECT 
    'Статистика тикетов (без изменений)' as info,
    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as new_tickets,
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as accepted_tickets,
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as assigned_tickets,
    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) as completed_tickets,
    COUNT(*) as total_tickets
FROM service_ticket;

-- Показать добавленные записи статусов
SELECT 
    'Добавленные записи статусов' as info,
    COUNT(*) as added_status_records
FROM service_ticket_statuses 
WHERE status_type = 3 
AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MINUTE);

-- Детальная информация о последних добавленных статусах
SELECT 
    sts.ticket_id,
    sts.status_type as completion_status,
    sts.admin_id,
    sts.created_at,
    st.status as ticket_status
FROM service_ticket_statuses sts
JOIN service_ticket st ON sts.ticket_id = st.id
WHERE sts.status_type = 3 
AND sts.created_at >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)
ORDER BY sts.ticket_id; 
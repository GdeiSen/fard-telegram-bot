from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, UTC
from utils.time_utils import now
from models import Object, Space, SpaceView

if TYPE_CHECKING:
    from database_manager import DatabaseManager

class SpacesService:
    def __init__(self, db: "DatabaseManager"):
        self.db = db
    
    # Методы для работы с объектами недвижимости (buildings)
    
    async def get_object(self, object_id: int) -> Optional[Object]:
        """Получить объект недвижимости по ID"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Object).filter_by(id=object_id))
                object_model = result.scalars().first()
                return object_model
        except SQLAlchemyError as e:
            print(f"Error in get_object: {e}")
            return None
    
    async def get_all_objects(self) -> List[Object]:
        """Получить все объекты недвижимости"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Object))
                object_models = result.scalars().all()
                return object_models
        except SQLAlchemyError as e:
            print(f"Error in get_all_objects: {e}")
            return []
    
    async def create_object(self, obj: Object) -> Optional[Object]:
        """Создать новый объект недвижимости"""
        try:
            async with self.db.Session() as session:
                obj.id = None
                session.add(obj)
                await session.commit()
                await session.refresh(obj)
                return obj
        except SQLAlchemyError as e:
            print(f"Error in create_object: {e}")
            return None
    
    async def update_object(self, obj: Object) -> Optional[Object]:
        """Обновить существующий объект недвижимости"""
        try:
            async with self.db.Session() as session:
                await session.merge(obj)
                await session.commit()
                return await self.get_object(obj.id)
        except SQLAlchemyError as e:
            print(f"Error in update_object: {e}")
            return None
    
    async def delete_object(self, object_id: int) -> bool:
        """Удалить объект недвижимости"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Object).filter_by(id=object_id))
                object_model = result.scalars().first()
                if object_model:
                    await session.delete(object_model)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error in delete_object: {e}")
            return False
    
    # Методы для работы с помещениями (spaces)
    
    async def get_space(self, space_id: int) -> Optional[Space]:
        """Получить помещение по ID"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Space).filter_by(id=space_id))
                space_model = result.scalars().first()
                return space_model
        except SQLAlchemyError as e:
            print(f"Error in get_space: {e}")
            return None
    
    async def get_spaces_by_object(self, object_id: int, only_available: bool = False) -> List[Space]:
        """Получить все помещения для конкретного объекта недвижимости
        
        Args:
            object_id: ID объекта недвижимости
            only_available: Если True, вернуть только доступные помещения
        """
        try:
            async with self.db.Session() as session:
                query = select(Space).filter_by(object_id=object_id)
                
                # Фильтр по доступности
                if only_available:
                    query = query.filter_by(is_available=True, status=True)
                
                result = await session.execute(query)
                space_models = result.scalars().all()
                return space_models
        except SQLAlchemyError as e:
            print(f"Error in get_spaces_by_object: {e}")
            return []
    
    async def create_space(self, space: Space) -> Optional[Space]:
        """Создать новое помещение"""
        try:
            async with self.db.Session() as session:
                space.id = None
                session.add(space)
                await session.commit()
                await session.refresh(space)
                return space
        except SQLAlchemyError as e:
            print(f"Error in create_space: {e}")
            return None
    
    async def update_space(self, space: Space) -> Optional[Space]:
        """Обновить существующее помещение"""
        try:
            async with self.db.Session() as session:
                await session.merge(space)
                await session.commit()
                return await self.get_space(space.id)
        except SQLAlchemyError as e:
            print(f"Error in update_space: {e}")
            return None
    
    async def delete_space(self, space_id: int) -> bool:
        """Удалить помещение"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Space).filter_by(id=space_id))
                space_model = result.scalars().first()
                if space_model:
                    await session.delete(space_model)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error in delete_space: {e}")
            return False
    
    async def change_space_availability(self, space_id: int, is_available: bool) -> bool:
        """Изменить доступность помещения (свободно/занято)"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Space).filter_by(id=space_id))
                space_model = result.scalars().first()
                if space_model:
                    space_model.is_available = is_available
                    space_model.updated_at = now()
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error in change_space_availability: {e}")
            return False
    
    async def change_space_status(self, space_id: int, status: bool) -> bool:
        """Изменить статус публикации помещения (опубликовано/скрыто)"""
        try:
            async with self.db.Session() as session:
                result = await session.execute(select(Space).filter_by(id=space_id))
                space_model = result.scalars().first()
                if space_model:
                    space_model.status = status
                    space_model.updated_at = now()
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            print(f"Error in change_space_status: {e}")
            return False
    
    # Методы для работы со счетчиками просмотров
    
    async def add_space_view(self, space_id: int, user_id: int) -> bool:
        """Добавить запись о просмотре помещения пользователем"""
        try:
            async with self.db.Session() as session:
                view = SpaceView(
                    id=None,  # None вместо 0, чтобы SQLAlchemy сама назначила ID
                    space_id=space_id,
                    user_id=user_id,
                    view_date=now()
                )
                session.add(view)
                await session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Error in add_space_view: {e}")
            return False
    
    async def get_space_views_stats(self, space_id: int, 
                               days: int = 7) -> Dict[str, Any]:
        """Получить статистику просмотров помещения за указанный период
        
        Args:
            space_id: ID помещения
            days: Количество дней для выборки статистики
        
        Returns:
            Dict с полями total_views, unique_users
        """
        try:
            async with self.db.Session() as session:
                # Определяем начальную дату для выборки
                start_date = now() - timedelta(days=days)
                
                # Запрос для получения всех просмотров за период
                views_query = select(SpaceView).filter(
                    SpaceView.space_id == space_id,
                    SpaceView.view_date >= start_date
                )
                
                result = await session.execute(views_query)
                views = result.scalars().all()
                
                # Считаем количество просмотров
                total_views = len(views)
                
                # Считаем уникальных пользователей
                unique_users = len(set(view.user_id for view in views))
                
                return {
                    "total_views": total_views,
                    "unique_users": unique_users
                }
        except SQLAlchemyError as e:
            print(f"Error in get_space_views_stats: {e}")
            return {"total_views": 0, "unique_users": 0} 
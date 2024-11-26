from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database
    from models import ServiceTicket
    from typing import List

class ServicesService:
    def __init__(self, db):
        self.db: Database = db

    async def get_service_tickets(self, user_id: int) -> "List[ServiceTicket]":
        return await self.db.get_service_tickets(user_id)

    async def create_service_ticket(self, service: "ServiceTicket") -> "ServiceTicket":
        test = await self.db.get_service_ticket(service.id)
        if test:
            return await self.update_service_ticket(service)
        await self.db.insert_service_ticket(service)
        return service

    async def update_service_ticket(self, service: "ServiceTicket") -> "ServiceTicket":
        await self.db.update_service_ticket(service)
        return service

    async def get_service_ticket(self, service_id: int) -> "ServiceTicket | None":
        service = await self.db.get_service_ticket(service_id)
        if service:
            return service
        return None

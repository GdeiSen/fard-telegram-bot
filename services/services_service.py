from objects import ServiceTicket

class ServicesService:
    def __init__(self, db):
        self.db = db
        
    async def get_service_tickets(self, user_id: int) -> list[ServiceTicket]:
        return self.db.get_service_tickets(user_id)
    
    async def create_service_ticket(self, service: ServiceTicket) -> ServiceTicket:
        test = self.db.get_service_ticket(service.id)
        if test:
            return await self.update_service_ticket(service)
        self.db.insert_service_ticket(service)
        return service
    
    async def update_service_ticket(self, service: ServiceTicket) -> ServiceTicket:
        self.db.update_service_ticket(service)
        return service
    
    async def remove_service_ticket(self, service: ServiceTicket):
        self.db.remove_service_ticket(service)
        
    async def get_service_ticket(self, service_id: int) -> ServiceTicket | None:
        service = self.db.get_service_ticket(service_id)
        if service:
            return service
        return None
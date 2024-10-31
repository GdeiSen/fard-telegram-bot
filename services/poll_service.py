from models import Dialog

class PollService:
    def __init__(self, db):
        self.db = db
        
    async def get_polls(self, user_id: int) -> list[Dialog]:
        return self.db.get_polls(user_id)
    
    async def create_poll(self, poll: Dialog) -> Dialog:
        test = self.db.get_poll(poll.id)
        if test:
            return await self.update_poll(poll)
        self.db.insert_poll(poll)
        return poll
    
    async def update_poll(self, poll: Dialog) -> Dialog:
        self.db.update_poll(poll)
        return poll
    
    async def remove_poll(self, poll: Dialog):
        self.db.remove_poll(poll)
        
    async def get_poll(self, poll_id: int) -> Dialog | None:
        poll = self.db.get_poll(poll_id)
        if poll:
            return poll
        return None
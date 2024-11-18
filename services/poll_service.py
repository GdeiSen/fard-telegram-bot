from models import Dialog
from models import Answer, User

class PollService:
    def __init__(self, db):
        self.db = db

    async def insert_answer(self, user: User, answer: Answer):
        await self.db.insert_answer(user, answer)

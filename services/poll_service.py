from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database
    from models import Answer, User
    from typing import List


class PollService:
    def __init__(self, db):
        self.db : Database = db

    async def insert_answer(self, user: "User", answer: "Answer"):
        await self.db.insert_answer(user, answer)

    async def update_answer(self, user: "User", answer: "Answer"):
        db_answer = await self.db.get_answer(user.id, answer.dialog_id, answer.sequence_id, answer.item_id)
        if db_answer is None:
            await self.insert_answer(user, answer)
        else:
            answer.id = db_answer.id
            await self.db.update_answer(user, answer)

    async def get_answers(self, user: "User") -> "List[Answer]":
        return await self.db.get_answers(user)

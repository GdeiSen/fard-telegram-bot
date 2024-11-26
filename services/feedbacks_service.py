from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database
    from models import Feedback


class FeedbacksService:
    def __init__(self, db):
        self.db: Database = db

    async def create_feedback(self, feedback: "Feedback") -> "Feedback":
        test = await self.db.get_feedback(feedback.id)
        if test:
            return await self.update_feedback(feedback)
        await self.db.insert_feedback(feedback)
        return feedback

    async def update_feedback(self, feedback: "Feedback") -> "Feedback":
        await self.db.update_feedback(feedback)
        return feedback

    async def remove_feedback(self, feedback: "Feedback"):
        await self.db.remove_feedback(feedback)

    async def get_feedback(self, feedback_id: int) -> "Feedback | None":
        feedback = await self.db.get_feedback(feedback_id)
        if feedback:
            return feedback
        return None

from models import Feedback

class FeedbacksService:
    def __init__(self, db):
        self.db = db

    async def get_feedbacks(self, user_id: int) -> list[Feedback]:
        return await self.db.get_feedbacks(user_id)

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        test = await self.db.get_feedback(feedback.id)
        if test:
            return await self.update_feedback(feedback)
        self.db.insert_feedback(feedback)
        return feedback

    async def update_feedback(self, feedback: Feedback) -> Feedback:
        await self.db.update_feedback(feedback)
        return feedback

    async def remove_feedback(self, feedback: Feedback):
        await self.db.remove_feedback(feedback)

    async def get_feedback(self, feedback_id: int) -> Feedback | None:
        feedback = await self.db.get_feedback(feedback_id)
        if feedback:
            return feedback
        return None

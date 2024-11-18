from datetime import datetime


class Answer:
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, question_id: int, answer: str, date: datetime):
        self.id = id
        self.user_id = user_id
        self.dialog_id = dialog_id,
        self.question_id = question_id
        self.sequence_id = sequence_id
        self.answer = answer
        self.created_at = date

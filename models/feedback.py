import datetime

class Feedback:
    def __init__(self, id: int, user_id: int, text: str, created_at: datetime.datetime):
        self.id = id
        self.user_id = user_id
        self.text = text
        self.created_at = created_at
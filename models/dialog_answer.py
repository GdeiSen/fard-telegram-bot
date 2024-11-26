class Answer:
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, item_id: int, answer: str, date: str):
        self.id = id
        self.user_id = user_id
        self.dialog_id = dialog_id
        self.item_id = item_id
        self.sequence_id = sequence_id
        self.answer = answer
        self.created_at = date

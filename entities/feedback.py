from entities.dialog_answer import Answer

class Feedback(Answer):
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, item_id: int, answer: str, text: str = None):
        super().__init__(id, user_id, dialog_id, sequence_id, item_id, answer)
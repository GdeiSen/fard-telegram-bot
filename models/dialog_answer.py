class Answer:
    def __init__(self, id: int, user_id: int, question_id: int, sequence_id: int, answer: str):
        self.id = id
        self.user_id = user_id
        self.question_id = question_id
        self.sequence_id = sequence_id
        self.answer = answer
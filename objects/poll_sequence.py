class Sequence:
    def __init__(self, id: int, questions_ids: list[int] = [], next_sequence_id: int | None = None):
        self.id = id
        self.questions_ids : list[int] = questions_ids
        self.next_sequence_id : int | None = next_sequence_id
class Question:
    def __init__(self, id: int, text: str, poll_id: int | None = None, answer: str | None = None, options_ids: list[int] | None = None):
        self.id = id
        self.text = text
        self.answer : str | None = answer
        self.options_ids : list[int] | None = options_ids   
        self.poll_id : int | None = poll_id
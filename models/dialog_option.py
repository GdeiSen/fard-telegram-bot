class Option:
    def __init__(self, id: int, text: str | None = None, sequence_id: int | None = None, row: int = 0):
        self.id = id
        self.text : str | None = text
        self.sequence_id : int | None = sequence_id
        self.row : int = row

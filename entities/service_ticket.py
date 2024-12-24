from entities.dialog_answer import Answer

class ServiceTicket(Answer):
    def __init__(self, id: int, user_id: int, dialog_id: int, sequence_id: int, item_id: int, answer: str, description: str, location: str, image: str | None = None, status: int = 0, details:str = None, header:str = None):
        super().__init__(id, user_id, dialog_id, sequence_id, item_id, answer)
        self.description = description
        self.location = location
        self.image = image
        self.status = status
        self.details = details
        self.header = header
class ServiceTicket:
    def __init__(self, id: int, user_id: int, description: str, location: str, image: str | None = None, checked: bool = False):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.location = location
        self.image = image
        self.checked = False
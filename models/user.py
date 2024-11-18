class User:
    def __init__(self, id: int, username: str, role: int | None):
        self.id: int = id
        self.username: str = username
        self.role: int | None = role
        self.first_name: str | None = None
        self.last_name: str | None = None
        self.middle_name: str | None = None
        self.language_code: str = "ru"
        self.data_processing_consent: bool = False
        self.object: str | None = None
        self.legal_entity: str |None = None

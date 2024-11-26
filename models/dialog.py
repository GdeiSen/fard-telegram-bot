from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import (Sequence, Question, Option)

class Dialog:
    def __init__(self, id: int, sequences: dict[int,"Sequence"] = {}, items:dict[int,"Question"] = {}, options:dict[int,"Option"] = {}):
        self.id = id
        self.sequences : dict[int,"Sequence"] = sequences
        self.items : dict[int,"Question"] = items
        self.options : dict[int,"Option"] = options

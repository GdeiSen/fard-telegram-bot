from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.dialog_sequence import DialogSequence
    from entities.dialog_item import DialogItem
    from entities.dialog_option import DialogOption

class Dialog:
    def __init__(self, id: int, sequences: dict[int,"Sequence"] = {}, items:dict[int,"Question"] = {}, options:dict[int,"Option"] = {}, trace:bool = False):
        self.id = id
        self.sequences : dict[int,"Sequence"] = sequences
        self.items : dict[int,"Question"] = items
        self.options : dict[int,"Option"] = options
        self.trace = trace

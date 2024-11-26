import json

from models import Sequence, Question, Option, Dialog

class DialogConverter:
    def convert(self, json_file: str) -> Dialog:
        with open(json_file, 'r') as file:
            data = json.load(file)
        sequences = {}
        items = {}
        options = {}
        for seq_data in data['sequences']:
            sequence = Sequence(
                id=seq_data['id'],
                items_ids=seq_data.get('items_ids'),
                next_sequence_id=seq_data.get('next_sequence_id'),
                dialog_id=seq_data.get('dialog_id')
            )
            sequences[sequence.id] = sequence
        for qst_data in data['items']:
            question = Question(
                id=qst_data['id'],
                text=qst_data.get('text'),
                options_ids=qst_data.get('options_ids'),
                type=qst_data.get('type')
            )
            items[question.id] = question
        for opt_data in data['options']:
            option = Option(
                id=opt_data['id'],
                text=opt_data.get('text'),
                sequence_id=opt_data.get('sequence_id'),
                row=opt_data.get('row') or 0,
            )
            options[option.id] = option
        dialog = Dialog(
            id=data['id'],
            sequences=sequences,
            items=items,
            options=options
        )

        return dialog

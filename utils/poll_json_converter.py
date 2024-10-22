import json

from objects import Sequence, Question, Option

from typing import (
    Dict, 
    Tuple
)

def json_to_sequences(json_file: str) -> Tuple[Dict[int, Sequence], Dict[int, Question], Dict[int, Option]]:
    with open(json_file, 'r') as file:
        data = json.load(file)
    sequences = {}
    questions = {}
    options = {}
    for seq_data in data['sequences']:
        sequence = Sequence(id=seq_data['id'], questions_ids=seq_data.get('questions_ids'), next_sequence_id=seq_data.get('next_sequence_id'))
        sequences[sequence.id] = sequence
    for qst_data in data['questions']:
        question = Question(id=qst_data['id'], text=qst_data.get('text'), answer=qst_data.get('answer'), options_ids=qst_data.get('options_ids'))
        questions[question.id] = question
    for opt_data in data['options']:
        option = Option(id=opt_data['id'], text=opt_data.get('text'), sequence_id=opt_data.get('sequence_id'))
        options[option.id] = option
    return sequences, questions, options
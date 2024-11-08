import argparse
import datetime
import logging
from typing import Awaitable, Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from assets.dict import Data
from database import Database
from models import (
    Answer,
    Dialog,
    Feedback,
    Option,
    Question,
    Sequence,
    ServiceTicket,
    User,
)
from services import FeedbacksService, PollService, ServicesService, UsersService
from utils import DictExtractor, json_to_sequences

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
locales = "./locales/localisation_uni.py"
poll = json_to_sequences(locales)
db = Database("database.db")
db.create_tables()

extractor = DictExtractor(Data)
feedbacks_service = FeedbacksService(db)
services_service = ServicesService(db)
poll_service = PollService(db)
users_service = UsersService(db)


def get_user_id(update: Update) -> int:
    try:
        return update.message.from_user.id
    except Exception:
        return update.callback_query.from_user.id


def set_buffer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message:
            context.user_data[BUFFER_MESSAGE] = update.message
        elif update.callback_query:
            context.user_data[BUFFER_MESSAGE] = update.callback_query.message
    except Exception as e:
        print(e)


async def delete_buffer_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message_td = context.user_data.get(BUFFER_MESSAGE)
    try:
        await context.bot.delete_message(
            chat_id=message_td.chat_id, message_id=message_td.message_id
        )
    except Exception:
        try:
            await context.bot.delete_message(
                chat_id=message_td.chat_id, message_id=message_td.message_id
            )
        except Exception:
            pass
    context.user_data[BUFFER_MESSAGE] = []


def get_text(
    key: str, payload: tuple[str] | None = None, group: str | None = "RU"
) -> str:
    text = extractor.get(key, payload) or key
    return text


async def send_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    payload: list[str] | None = None,
) -> None:
    text = get_text(text, payload, "RU")
    try:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    except Exception:
        try:
            await update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        except Exception:
            try:
                await context.bot.send_message(
                    update.message.chat_id,
                    text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await context.bot.send_message(
                    update.callback_query.message.chat_id,
                    text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )


def create_keyboard(rows: list[list[tuple[str, int | str]]]) -> InlineKeyboardMarkup:
    keyboard = []
    for row in rows:
        keyboard_row = []
        for item in row:
            text = get_text(item[0])
            callback_data = item[1]
            keyboard_row.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)


async def poll_answer_save_callback(
    dialog_id: int,
    sequence_id: int,
    question_id: int,
    option_id: int | None,
    answer: str | None,
    state: int,
) -> None:
    print(
        f"Poll answer save callback: {dialog_id}, {sequence_id}, {question_id}, {option_id}, {answer}, {state}"
    )


async def service_answer_save_callback(
    dialog_id: int,
    sequence_id: int,
    question_id: int,
    option_id: int,
    answer: str,
    state: int,
) -> None:
    pass


LPR_ROLE = 10011
MA_ROLE = 20122

SELECTING_ACTION = 1
(
    SELECTING_SERVICE_ACTION,
    SELECTING_PROFILE_ACTION,
    SELECTING_POLLING_ACTION,
    SELECTING_FEEDBACK_ACTION,
) = range(100, 104)

(
    SETTING_SERVICE_DESCRIPTION,
    SETTING_SERVICE_DESCRIPTION_LOCATION,
    SETTING_SERVICE_DESCRIPTION_IMAGE,
    SENDING_SERVICE,
    SETTING_PROFILE_NAME,
    SETTING_PROFILE_OBJECT,
    SETTING_PROFILE_LEGAL_ENTITY,
    POLLING,
    SETTING_POLL_QUESTION,
    SENDING_POLL_ANSWER,
    SETTING_FEEDBACK,
    SENDING_FEEDBACK,
) = range(200, 212)

(TYPING, UPLOADING, CANCELING, CLEARING) = range(300, 304)

END = ConversationHandler.END

(
    BUFFER_DESCRIPTION,
    BUFFER_LOCATION,
    BUFFER_IMAGE,
    ACTIVE_INPUT_MODE,
    BUFFER_MESSAGE,
    BUFFER_NAME,
    BUFFER_LEGAL_ENTITY,
    BUFFER_OBJECT,
    BUFFER_POLL_QUESTION,
    BUFFER_POLL,
    BUFFER_DIALOG_ANSWER,
    BUFFER_QUESTION_MESSAGE,
    ACTIVE_MULTI_DIALOG_SEQUENCE_ID,
    ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX,
    ACTIVE_MULTI_DIALOG,
    BUFFER_FEEDBACK,
    BUFFER_DIALOG_ANSWERS,
    BUFFER_LANGUAGE,
    FIRST_START,
    STATUS,
) = range(400, 420)

_constates_map = {
    SETTING_SERVICE_DESCRIPTION: BUFFER_DESCRIPTION,
    SETTING_SERVICE_DESCRIPTION_LOCATION: BUFFER_LOCATION,
    SETTING_PROFILE_OBJECT: BUFFER_OBJECT,
    SETTING_PROFILE_NAME: BUFFER_NAME,
    SETTING_PROFILE_LEGAL_ENTITY: BUFFER_LEGAL_ENTITY,
    SETTING_POLL_QUESTION: BUFFER_DIALOG_ANSWER,
    SETTING_FEEDBACK: BUFFER_FEEDBACK,
    UPLOADING: BUFFER_IMAGE,
    SETTING_SERVICE_DESCRIPTION_IMAGE: BUFFER_IMAGE,
}
_service_input_modes = [
    SETTING_SERVICE_DESCRIPTION,
    SETTING_SERVICE_DESCRIPTION_LOCATION,
    SETTING_SERVICE_DESCRIPTION_IMAGE,
]
_profile_input_modes = [
    SETTING_PROFILE_NAME,
    SETTING_PROFILE_OBJECT,
    SETTING_PROFILE_LEGAL_ENTITY,
]
_polling_input_modes = [SETTING_POLL_QUESTION, SENDING_POLL_ANSWER]
_feedback_input_modes = [SETTING_FEEDBACK]
_multi_dialogs_callbacks = {
    SETTING_POLL_QUESTION: poll_answer_save_callback,
    SENDING_POLL_ANSWER: poll_answer_save_callback,
    SETTING_SERVICE_DESCRIPTION: service_answer_save_callback,
    SETTING_SERVICE_DESCRIPTION_LOCATION: service_answer_save_callback,
    SETTING_SERVICE_DESCRIPTION_IMAGE: service_answer_save_callback,
    SENDING_SERVICE: service_answer_save_callback,
}


async def start_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if update.message.chat.type != "private":
        return END
    payload = context.args[0] if context.args else None
    user_id = update.message.from_user.id
    user = await users_service.get_user(user_id)
    context.user_data[BUFFER_DIALOG_ANSWERS] = []
    if user is None:
        user = User(user_id, update.message.from_user.username, None)
        user = await users_service.create_user(user)
    last_name = user.last_name if user.last_name else None
    first_name = user.first_name if user.first_name else None
    middle_name = user.middle_name if user.middle_name else None
    object = user.object if user.object else ""
    legal_entity = user.legal_entity if user.legal_entity else ""
    context.user_data[BUFFER_OBJECT] = object
    context.user_data[BUFFER_LEGAL_ENTITY] = legal_entity

    # NEED TO BE OPTIMIZED
    if last_name and middle_name and first_name:
        context.user_data[BUFFER_NAME] = (
            last_name + " " + first_name + " " + middle_name
        )
    else:
        context.user_data[BUFFER_NAME] = None
    #
    try:
        context.user_data[FIRST_START]
    except KeyError:
        context.user_data[FIRST_START] = True
    if context.user_data[FIRST_START]:
        if payload == str(LPR_ROLE):
            user.role = LPR_ROLE
            await send_message(update, context, "profile_identification_completed")
        elif payload == str(MA_ROLE):
            user.role = MA_ROLE
            await send_message(update, context, "profile_identification_completed")
        else:
            await send_message(update, context, "user_profile_identification_error")
        await users_service.update_user(user)
        await send_message(
            update,
            context,
            "user_agreement_input_handler_prompt",
            create_keyboard([[("agree", SELECTING_ACTION)]]),
        )
        context.user_data[FIRST_START] = False
        return SELECTING_ACTION
    else:
        await send_message(
            update,
            context,
            "data_sync_completed",
            create_keyboard([[("continue", SELECTING_ACTION)]]),
        )
        return SELECTING_ACTION


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    name = context.user_data.get(BUFFER_NAME)
    legal_entity = context.user_data.get(BUFFER_LEGAL_ENTITY)
    object = context.user_data.get(BUFFER_OBJECT)
    # first_name = (" " + name.split(" ")[1]) if name else ""
    # middle_name = name.split(" ")[2] if name else ""
    user_id = get_user_id(update)
    user = await users_service.get_user(user_id)
    if not name or not legal_entity or not object:
        message = get_text("user_profile_validation_error")
    else:
        message = ""
    keyboard = create_keyboard(
        [
            [
                (
                    "profile" if message == "" else "profile_warn",
                    SELECTING_PROFILE_ACTION,
                ),
                ("service", SELECTING_SERVICE_ACTION),
                ("polling", SELECTING_POLLING_ACTION),
                ("feedback", SELECTING_FEEDBACK_ACTION),
            ]
        ]
    )

    text = "default_greeting"
    if user.role == MA_ROLE:
        text = "ma_greeting"
        keyboard = create_keyboard(
            [
                [
                    (
                        "profile" if message == "" else "profile_warn",
                        SELECTING_PROFILE_ACTION,
                    ),
                    ("service", SELECTING_SERVICE_ACTION),
                ]
            ]
        )
    await send_message(update, context, text, keyboard, payload=(message,))
    return SELECTING_ACTION

# TO DO (implement multi_dialog and remove previous system)
async def start_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    current_problem = context.user_data.get(BUFFER_DESCRIPTION) or "не указано"
    current_location = context.user_data.get(BUFFER_LOCATION) or "не указано"
    current_image = "не прикреплено"
    if context.user_data.get(BUFFER_IMAGE):
        current_image = "прикреплено"
    await send_message(
        update,
        context,
        "service_header",
        create_keyboard(
            [
                [
                    ("description", SETTING_SERVICE_DESCRIPTION),
                    ("location", SETTING_SERVICE_DESCRIPTION_LOCATION),
                    ("image", SETTING_SERVICE_DESCRIPTION_IMAGE),
                ],
                [("back", SELECTING_ACTION), ("send", SENDING_SERVICE)],
            ]
        ),
        payload=[current_problem, current_location, current_image],
    )
    return SELECTING_SERVICE_ACTION

# TO DO (implement multi_dialog and remove previous system)
async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    buffer_name = context.user_data.get(BUFFER_NAME)
    buffer_object = context.user_data.get(BUFFER_OBJECT)
    buffer_legal_entity = context.user_data.get(BUFFER_LEGAL_ENTITY)
    user_id = get_user_id(update)
    user = await users_service.get_user(user_id)
    if user:
        if buffer_name:
            last_name = buffer_name.split(" ")[0]
            first_name = (
                buffer_name.split(" ")[1] if len(buffer_name.split(" ")) > 1 else ""
            )
            middle_name = (
                buffer_name.split(" ")[2] if len(buffer_name.split(" ")) > 2 else ""
            )
            user.first_name = first_name
            user.last_name = last_name
            user.middle_name = middle_name
            await users_service.update_user(user)
        if buffer_object:
            object = buffer_object
            user.object = object
            await users_service.update_user(user)
        if buffer_legal_entity:
            legal_entity = buffer_legal_entity
            user.legal_entity = legal_entity
            await users_service.update_user(user)
    await send_message(
        update,
        context,
        "profile_header",
        create_keyboard(
            [
                [
                    ("name", SETTING_PROFILE_NAME),
                    ("legal_entity", SETTING_PROFILE_LEGAL_ENTITY),
                    ("object", SETTING_PROFILE_OBJECT),
                ],
                [("back", SELECTING_ACTION)],
            ]
        ),
        payload=[buffer_name or "-", buffer_legal_entity or "-", buffer_object or "-"],
    )
    return SELECTING_PROFILE_ACTION


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    set_buffer_message(update, context)
    buffer = context.user_data.get(BUFFER_FEEDBACK) or "отсутствует"
    await send_message(
        update,
        context,
        "feedback_header",
        create_keyboard(
            [
                [
                    ("edit", SETTING_FEEDBACK),
                    ("send", SENDING_FEEDBACK),
                    ("cancel", SELECTING_ACTION),
                ]
            ]
        ),
        payload=[buffer],
    )
    return SELECTING_FEEDBACK_ACTION


async def start_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_MULTI_DIALOG] = poll
    context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_ID] = 0
    context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
    text = "poll_header"
    await send_message(
        update,
        context,
        text,
        create_keyboard(
            [[("start", SETTING_POLL_QUESTION), ("cancel", SELECTING_ACTION)]]
        ),
    )
    return SETTING_POLL_QUESTION


async def set_multi_dialog_item(
    update: Update, context: ContextTypes.DEFAULT_TYPE, save_mode: int = 0
) -> int:
    active_input_mode: int = context.user_data.get(ACTIVE_INPUT_MODE)
    # active_multi_dialog = context.user_data.get(ACTIVE_MULTI_DIALOG)
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    keyboard = create_keyboard([[("back", SELECTING_ACTION)]])
    dialog = context.user_data.get(ACTIVE_MULTI_DIALOG)
    if dialog is None:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION
    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_MULTI_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(
        ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX
    )
    if active_sequence_id is None or active_sequence_question_index is None:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION
    active_sequence = sequences.get(active_sequence_id)
    if not active_sequence or not active_sequence.questions_ids:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION
    active_questions = [questions[i] for i in active_sequence.questions_ids]
    if active_sequence_question_index >= len(active_questions):
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION
    active_question = active_questions[active_sequence_question_index]
    args = None
    if update.callback_query:
        callback_data = update.callback_query.data.split(":")
        try:
            args = int(callback_data[1]) if len(callback_data) > 1 else None
        except ValueError:
            args = None
    text_input = context.user_data.pop(BUFFER_DIALOG_ANSWER, None)
    answer: str | None = None
    if text_input:
        answer = text_input
        context.user_data[BUFFER_DIALOG_ANSWER] = None
    elif args is not None:
        answer = options.get(args).text
    print(f"Text input: {text_input}")
    print(f"Args: {args}")
    print(f"Answer: {answer}")
    print(f"Callback: {_multi_dialogs_callbacks.get(active_input_mode)}")
    if answer and _multi_dialogs_callbacks.get(active_input_mode):
        await _multi_dialogs_callbacks.get(active_input_mode)(
            active_sequence.dialog_id,
            active_sequence.id,
            active_question.id,
            args,
            answer,
            0,
        )
    if args is not None or text_input:
        index = active_questions.index(active_question)
        selected_option = options.get(args)
        if selected_option and selected_option.sequence_id is not None:
            context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_ID] = (
                selected_option.sequence_id
            )
            context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
        elif index + 1 < len(active_questions):
            context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX] = index + 1
        elif active_sequence.next_sequence_id is not None:
            context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_ID] = (
                active_sequence.next_sequence_id
            )
            context.user_data[ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
        else:
            await send_message(update, context, "multi_dialog_completed")
            if _multi_dialogs_callbacks.get(active_input_mode):
                await _multi_dialogs_callbacks.get(active_input_mode)(
                    active_sequence.dialog_id,
                    active_sequence.id,
                    active_question.id,
                    args,
                    answer,
                    1,
                )
            await start_menu(update, context)
            return SELECTING_POLLING_ACTION
        active_sequence_id = context.user_data.get(ACTIVE_MULTI_DIALOG_SEQUENCE_ID)
        active_sequence_question_index = context.user_data.get(
            ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX
        )
        active_sequence = sequences.get(active_sequence_id)
        if not active_sequence:
            await send_message(update, context, "multi_dialog_data_error")
            return SELECTING_ACTION
        active_questions = [questions[i] for i in active_sequence.questions_ids]
        if active_sequence_question_index < len(active_questions):
            active_question = active_questions[active_sequence_question_index]
        else:
            active_question = None
    keyboard = create_keyboard(
        [[("send", SENDING_POLL_ANSWER), ("cancel", SELECTING_ACTION)]]
    )
    question_text = active_question.text if active_question else "No question data"
    await send_message(update, context, question_text, keyboard)

    return SETTING_POLL_QUESTION


async def set_multi_dialog_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_POLL_QUESTION
    dialog = context.user_data.get(ACTIVE_MULTI_DIALOG)

    if dialog is None:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION

    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_MULTI_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(
        ACTIVE_MULTI_DIALOG_SEQUENCE_QUESTION_INDEX
    )

    if active_sequence_id is None or active_sequence_question_index is None:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION

    active_sequence = sequences.get(active_sequence_id)
    if not active_sequence or not active_sequence.questions_ids:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION

    if active_sequence_question_index >= len(active_sequence.questions_ids):
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION

    active_question_index = active_sequence.questions_ids[
        active_sequence_question_index
    ]
    active_question = questions.get(active_question_index)

    if active_question is None:
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_ACTION

    active_options = [
        options[i] for i in (active_question.options_ids or []) if i in options
    ]

    options_buf = []
    for option in active_options:
        options_buf.append(
            (option.text, str(SETTING_POLL_QUESTION) + ":" + str(option.id))
        )
    options_buf.append(("cancel", SELECTING_ACTION))
    keyboard = create_keyboard([options_buf])
    await send_message(
        update, context, "multi_dialog_question_text_handler_prompt", keyboard
    )
    if update.callback_query:
        set_buffer_message(update, context)

    return TYPING


async def set_profile_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_NAME
    keyboard = create_keyboard([[("back", SELECTING_ACTION)], [("clear", CLEARING)]])
    await send_message(
        update,
        context,
        "profile_name_text_handler_prompt",
        keyboard,
    )
    set_buffer_message(update, context)
    return TYPING


async def set_profile_legal_entity(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "multi_dialog_data_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_LEGAL_ENTITY
    keyboard = create_keyboard(
        [
            [
                ("back", SELECTING_ACTION),
                ("clear", CLEARING),
            ]
        ]
    )
    await send_message(
        update, context, "profile_legal_entity_text_handler_prompt", keyboard
    )
    set_buffer_message(update, context)
    return TYPING


async def set_profile_object(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_OBJECT
    args = update.callback_query.data.split(":")
    args = args[1] if len(args) > 1 else None
    if args:
        if args == "1":
            context.user_data[BUFFER_OBJECT] = "БЦ 'Основателей'"
        elif args == "2":
            context.user_data[BUFFER_OBJECT] = "МФК 'Нордсити'"
        elif args == "3":
            context.user_data[BUFFER_OBJECT] = "Стелла"
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION
    keyboard = create_keyboard(
        [
            [
                ("БЦ 'Основателей'", str(SETTING_PROFILE_OBJECT) + ":1"),
            ],
            [
                ("МФК 'Нордсити'", str(SETTING_PROFILE_OBJECT) + ":2"),
            ],
            [
                ("Стелла", str(SETTING_PROFILE_OBJECT) + ":3"),
            ],
            [("Отмена", CANCELING)],
        ]
    )
    await send_message(update, context, "profile_object_text_handler_prompt", keyboard)
    set_buffer_message(update, context)
    return SELECTING_PROFILE_ACTION


async def set_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_FEEDBACK
    keyboard = create_keyboard([[("cancel", CANCELING)]])
    await send_message(update, context, "feedback_text_handler_prompt", keyboard)
    set_buffer_message(update, context)
    return TYPING


async def send_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    buffer = context.user_data.get(BUFFER_FEEDBACK) or None
    text = None
    if (
        context.user_data.get(BUFFER_NAME) is None
        or context.user_data.get(BUFFER_LEGAL_ENTITY) is None
        or context.user_data.get(BUFFER_OBJECT) is None
    ):
        text = "user_profile_validation_error"
    elif buffer:
        feedback = await feedbacks_service.create_feedback(
            Feedback(
                0,
                user_id=get_user_id(update),
                text=buffer,
                created_at=datetime.datetime.now(),
            )
        )
        text = "feedback_completed"
        context.user_data[BUFFER_FEEDBACK] = None
    else:
        text = "feedback_data_error"
    keyboard = create_keyboard([[("cancel", SELECTING_FEEDBACK_ACTION)]])
    await send_message(update, context, text, keyboard)
    return SELECTING_FEEDBACK_ACTION


async def set_service_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION
    keyboard = create_keyboard(
        [
            [
                ("back", SELECTING_ACTION),
                ("clear", CLEARING),
            ]
        ]
    )

    await send_message(
        update, context, "service_description_text_handler_prompt", keyboard
    )
    set_buffer_message(update, context)
    return TYPING


async def set_service_location(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION_LOCATION
    keyboard = create_keyboard(
        [
            [
                ("back", SELECTING_ACTION),
                ("clear", CLEARING),
            ]
        ]
    )
    await send_message(
        update, context, "service_location_text_handler_prompt", keyboard
    )
    set_buffer_message(update, context)
    return TYPING


async def set_service_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION_IMAGE
    keyboard = create_keyboard(
        [
            [
                ("back", SELECTING_ACTION),
                ("clear", CLEARING),
            ]
        ]
    )
    await send_message(update, context, "service_image_text_handler_prompt", keyboard)
    set_buffer_message(update, context)
    return UPLOADING

# NEED TO BE REMOVED
async def send_service_ticket(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    description = context.user_data.get(BUFFER_DESCRIPTION) or None
    location = context.user_data.get(BUFFER_LOCATION) or None
    image = context.user_data.get(BUFFER_IMAGE) or None
    keyboard = create_keyboard([[("back", SELECTING_SERVICE_ACTION)]])
    if description is None or location is None:
        await send_message(
            update,
            context,
            "service_data_error",
            keyboard,
        )
        return SELECTING_SERVICE_ACTION
    elif (
        context.user_data.get(BUFFER_NAME) is None
        or context.user_data.get(BUFFER_LEGAL_ENTITY) is None
        or context.user_data.get(BUFFER_OBJECT) is None
    ):
        await send_message(
            update,
            context,
            "user_profile_validation_error",
            keyboard,
        )
        return SELECTING_SERVICE_ACTION
    service_ticket = await services_service.create_service_ticket(
        ServiceTicket(
            0,
            user_id=get_user_id(update),
            description=description,
            location=location,
            image=image,
            checked=False,
        )
    )
    await send_message(
        update,
        context,
        "service_ticket_completed",
        keyboard,
    )
    context.user_data[BUFFER_DESCRIPTION] = None
    context.user_data[BUFFER_LOCATION] = None
    context.user_data[BUFFER_IMAGE] = None
    return SELECTING_SERVICE_ACTION


async def handle_text_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | str:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    if not validate_message(update):
        await send_message(update, context, "message_data_validation_error")
        return SELECTING_SERVICE_ACTION
    user_text = update.message.text.strip()
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)

    if active_input_mode in _constates_map:
        context.user_data[_constates_map[active_input_mode]] = user_text

    await delete_buffer_message(update, context)

    if active_input_mode in _service_input_modes:
        if not validate_service_location(context):
            await send_message(
                update,
                context,
                "text_length_validation_error",
            )
            context.user_data[BUFFER_LOCATION] = None
        elif not validate_service_description(context):
            await send_message(
                update,
                context,
                "text_length_validation_error",
            )
            context.user_data[BUFFER_DESCRIPTION] = None
        await start_service(update, context)
        return SELECTING_SERVICE_ACTION

    elif active_input_mode in _profile_input_modes:
        if not validate_profile_object(context):
            await send_message(update, context, "text_length_validation_error")
            context.user_data[BUFFER_OBJECT] = None
        elif not validate_profile_name(context):
            await send_message(
                update,
                context,
                "⚠️ Имя должно быть в формате: Фамилия Имя Отчество\nИли фамилия должна быть не менее 3-х символов, и общее количество не более 50 символов.",
            )
            context.user_data[BUFFER_NAME] = None
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION

    elif active_input_mode in _polling_input_modes:
        if not validate_question_text(context):
            await send_message(update, context, "text_length_validation_error")
            context.user_data[BUFFER_DIALOG_ANSWER] = None
        await set_multi_dialog_item(update, context)
        return SETTING_POLL_QUESTION

    elif active_input_mode in _feedback_input_modes:
        await start_feedback(update, context)
        return SELECTING_FEEDBACK_ACTION

    context.user_data[ACTIVE_INPUT_MODE] = None
    return SELECTING_ACTION


def validate_user_data(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data is not None


def validate_message(update: Update) -> bool:
    return update.message is not None


def validate_callback_query(update: Update) -> bool:
    return update.callback_query is not None


def validate_question_text(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if validate_user_data(context):
        question_text = context.user_data.get(BUFFER_DIALOG_ANSWER, "")
        return question_text is None or len(question_text) <= 1000


def validate_service_description(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if validate_user_data(context):
        description = context.user_data.get(BUFFER_DESCRIPTION, "")
        return description is None or len(description) <= 1000
    return False


def validate_service_location(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if validate_user_data(context):
        location = context.user_data.get(BUFFER_LOCATION, "")
        return location is None or len(location) <= 1000
    return False


def validate_profile_object(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if validate_user_data(context):
        profile_object = context.user_data.get(BUFFER_OBJECT, "")
        return profile_object is None or len(profile_object) <= 1000
    return False


def validate_profile_name(context: ContextTypes.DEFAULT_TYPE) -> bool:
    if validate_user_data(context):
        buffer_name = context.user_data.get(BUFFER_NAME, "")
        if not buffer_name:
            return False
        parts = buffer_name.split(" ")
        return (
            len(parts) == 3
            and len(parts[0]) >= 3
            and sum(len(part) for part in parts) <= 50
        )
    return False


async def handle_image_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data is None:
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    if update.message is None:
        await send_message(update, context, "message_data_validation_error")
        return SELECTING_SERVICE_ACTION
    try:
        await delete_buffer_message(update, context)
        photo_file = await update.message.photo[-1].get_file()
        context.user_data[BUFFER_IMAGE] = photo_file.file_id
        logger.info(f"Image received and stored with file_id: {photo_file.file_id}")
    except (IndexError, AttributeError) as e:
        logger.error(f"Failed to process image input: {e}")
        await send_message(update, context, "message_data_validation_error")
        return SELECTING_SERVICE_ACTION

    await start_service(update, context)
    return SELECTING_SERVICE_ACTION


async def cancel_text_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    if context.user_data is None:
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_ACTION

    await send_message(update, context, "Canceled")
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    if active_input_mode:
        if active_input_mode in _service_input_modes:
            await start_service(update, context)
            return SELECTING_SERVICE_ACTION
        if active_input_mode in _profile_input_modes:
            await start_profile(update, context)
            return SELECTING_PROFILE_ACTION
        if active_input_mode in _polling_input_modes:
            await start_poll(update, context)
            return SELECTING_POLLING_ACTION
        if active_input_mode in _feedback_input_modes:
            await start_feedback(update, context)
            return SELECTING_FEEDBACK_ACTION


async def clear_text_buffer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    if context.user_data is None:
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_ACTION
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    if active_input_mode:
        context.user_data[_constates_map[active_input_mode]] = None
    await send_message(update, context, "Canceled")
    if active_input_mode in _service_input_modes:
        await start_service(update, context)
        return SELECTING_SERVICE_ACTION
    if active_input_mode in _profile_input_modes:
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION
    if active_input_mode in _polling_input_modes:
        await start_poll(update, context)
        return SELECTING_POLLING_ACTION


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the bot with a specified Telegram token."
    )
    parser.add_argument("token", help="The Telegram bot token")

    args = parser.parse_args()
    application = Application.builder().token(args.token).build()
    service_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_service, pattern="^" + str(SELECTING_SERVICE_ACTION) + "$"
            )
        ],
        states={
            UPLOADING: [MessageHandler(filters.PHOTO, handle_image_input)],
            TYPING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            SELECTING_SERVICE_ACTION: [
                CallbackQueryHandler(
                    set_service_description,
                    pattern="^" + str(SETTING_SERVICE_DESCRIPTION) + "$",
                ),
                CallbackQueryHandler(
                    set_service_location,
                    pattern="^" + str(SETTING_SERVICE_DESCRIPTION_LOCATION) + "$",
                ),
                CallbackQueryHandler(
                    set_service_image,
                    pattern="^" + str(SETTING_SERVICE_DESCRIPTION_IMAGE) + "$",
                ),
                CallbackQueryHandler(
                    send_service_ticket, pattern="^" + str(SENDING_SERVICE) + "$"
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(
                start_service, pattern="^" + str(SELECTING_SERVICE_ACTION) + "$"
            ),
        ],
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    profile_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_profile, pattern="^" + str(SELECTING_PROFILE_ACTION) + "$"
            )
        ],
        states={
            TYPING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            SELECTING_PROFILE_ACTION: [
                CallbackQueryHandler(
                    set_profile_name, pattern="^" + str(SETTING_PROFILE_NAME) + "$"
                ),
                CallbackQueryHandler(
                    set_profile_legal_entity,
                    pattern="^" + str(SETTING_PROFILE_LEGAL_ENTITY) + "$",
                ),
                CallbackQueryHandler(
                    set_profile_object,
                    pattern="^" + str(SETTING_PROFILE_OBJECT) + r":?(\d+)?$",
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(
                start_service, pattern="^" + str(SELECTING_PROFILE_ACTION) + "$"
            ),
        ],
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    polling_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_poll, pattern="^" + str(SELECTING_POLLING_ACTION) + "$"
            )
        ],
        states={
            TYPING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            SENDING_POLL_ANSWER: [
                CallbackQueryHandler(
                    set_multi_dialog_answer,
                    pattern="^" + str(SENDING_POLL_ANSWER) + "$",
                )
            ],
            SETTING_POLL_QUESTION: [
                CallbackQueryHandler(
                    set_multi_dialog_item,
                    pattern="^" + str(SETTING_POLL_QUESTION) + r":?(\d+)?$",
                )
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                set_multi_dialog_answer, pattern="^" + str(SENDING_POLL_ANSWER) + "$"
            ),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(
                set_multi_dialog_item,
                pattern="^" + str(SETTING_POLL_QUESTION) + r":?(\d+)?$",
            ),
        ],
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    feedback_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_feedback, pattern="^" + str(SELECTING_FEEDBACK_ACTION) + "$"
            )
        ],
        states={
            TYPING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            SELECTING_FEEDBACK_ACTION: [
                CallbackQueryHandler(
                    set_feedback, pattern="^" + str(SETTING_FEEDBACK) + "$"
                ),
                CallbackQueryHandler(
                    send_feedback, pattern="^" + str(SENDING_FEEDBACK) + "$"
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(
                start_feedback, pattern="^" + str(SELECTING_FEEDBACK_ACTION) + "$"
            ),
        ],
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    main_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CommandHandler("menu", start_menu),
        ],
        states={
            SELECTING_ACTION: [
                profile_conv_handler,
                service_conv_handler,
                polling_conv_handler,
                feedback_conv_handler,
            ]
        },
        fallbacks=[
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$")
        ],
    )
    application.add_handler(main_conv_handler)
    application.add_handler(CommandHandler("start", start_app))
    application.add_handler(CommandHandler("menu", start_menu))
    application.run_polling()


if __name__ == "__main__":
    main()

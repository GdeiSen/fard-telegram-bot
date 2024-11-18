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

from locales.localisation_uni import Data as LocalisationData
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
poll_dialog = json_to_sequences("./assets/poll_dialog.json")
service_dialog = json_to_sequences("./assets/service_dialog.json")
profile_dialog = json_to_sequences("./assets/profile_dialog.json")
db = Database("database.db")
db.create_tables()

extractor = DictExtractor(LocalisationData)
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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dialog_id: int,
    sequence_id: int,
    question_id: int,
    option_id: int | None,
    answer: str | None,
    state: int,
) -> None:
    user_id = get_user_id(update)
    user = await users_service.get_user(user_id)
    answer_obj = Answer(0, user_id, dialog_id, sequence_id, question_id, answer, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(answer_obj.id)
    print(answer_obj.user_id)
    answer_obj.dialog_id = answer_obj.dialog_id[0]
    print(answer_obj.sequence_id)
    print(answer_obj.question_id)
    print(answer_obj.answer)
    print(answer_obj.created_at)
    await poll_service.insert_answer(user, answer_obj)


async def service_answer_save_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dialog_id: int,
    sequence_id: int,
    question_id: int,
    option_id: int,
    answer: str,
    state: int,
) -> None:
    user_id = get_user_id(update)
    user:User = await users_service.get_user(user_id)
    print(dialog_id)
    print(sequence_id)
    print(question_id)
    print(option_id)
    print(answer)
    print(state)


async def profile_answer_save_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dialog_id: int,
    sequence_id: int,
    question_id: int,
    option_id: int,
    answer: str,
    state: int,
) -> None:
    user_id = get_user_id(update)
    user:User = await users_service.get_user(user_id)
    if question_id == 0:
        user.last_name = answer
    elif question_id == 1:
        user.first_name = answer
    elif question_id == 2:
        user.middle_name = answer
    elif question_id == 3:
        user.legal_entity = answer
    await users_service.update_user(user)
    context.user_data[USER_NAME] = (
        (user.last_name or "") + " " +
        (user.first_name or "") + " " +
        (user.middle_name or "")
    ).strip()
    context.user_data[USER_LEGAL_ENTITY] = user.legal_entity


LPR_ROLE = 10011
MA_ROLE = 20122

SELECTING_ACTION = 1
(
    SELECTING_SERVICE_ACTION,
    SELECTING_PROFILE_ACTION,
    SELECTING_POLL_ACTION,
    SELECTING_FEEDBACK_ACTION,
) = range(100, 104)

(
    SETTING_SERVICE_DESCRIPTION,
    SETTING_SERVICE_DESCRIPTION_LOCATION,
    SETTING_SERVICE_DESCRIPTION_IMAGE,
    SENDING_SERVICE,
    SETTING_USER_NAME,
    SETTING_PROFILE_OBJECT,
    SETTING_PROFILE_LEGAL_ENTITY,
    SETTING_DIALOG_ITEM,
    SELECTING_DIALOG_ANSWER,
    SELECTING_POLL_ACTION,
    TYPING_DIALOG_ANSWER,
    UPLOADING_DIALOG_ANSWER,
    CANCELING_DIALOG_ITEM,
    SETTING_FEEDBACK,
    SENDING_FEEDBACK,
) = range(200, 215)

(
    TYPING,
    UPLOADING,
    CANCELING,
    CLEARING,
    SELECTING
) = range(300, 305)

END = ConversationHandler.END

(
    SERVICE_DESCRIPTION,
    SERVICE_LOCATION,
    SERVICE_IMAGE,
    ACTIVE_INPUT_MODE,
    BUFFER_IMAGE,
    BUFFER_MESSAGE,
    USER_NAME,
    USER_LEGAL_ENTITY,
    USER_OBJECT,
    BUFFER_POLL,
    BUFFER_DIALOG_ANSWER,
    ACTIVE_DIALOG_SEQUENCE_ID,
    ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX,
    ACTIVE_DIALOG,
    ACTIVE_DIALOG_TRACE,
    FEEDBACK_BUFFER,
    FIRST_START
) = range(400, 417)


_text_handler_routes_map = {
    SELECTING_FEEDBACK_ACTION: FEEDBACK_BUFFER,
    SELECTING_POLL_ACTION: BUFFER_DIALOG_ANSWER,
    SELECTING_PROFILE_ACTION: BUFFER_DIALOG_ANSWER,
    SELECTING_SERVICE_ACTION: BUFFER_DIALOG_ANSWER
}
_image_handler_routes_map = {
    SETTING_DIALOG_ITEM: BUFFER_IMAGE,
    SELECTING_POLL_ACTION: BUFFER_IMAGE,
    SELECTING_PROFILE_ACTION: BUFFER_IMAGE,
    SELECTING_SERVICE_ACTION: BUFFER_IMAGE
}
_service_input_modes = [
    SETTING_SERVICE_DESCRIPTION,
    SETTING_SERVICE_DESCRIPTION_LOCATION,
    SETTING_SERVICE_DESCRIPTION_IMAGE,
]
_profile_input_modes = [
    SETTING_USER_NAME,
    SETTING_PROFILE_OBJECT,
    SETTING_PROFILE_LEGAL_ENTITY,
]
_polling_input_modes = [
    SETTING_DIALOG_ITEM,
    SELECTING_DIALOG_ANSWER
]
_feedback_input_modes = [
    SETTING_FEEDBACK
]
_dialog_callbacks = {
    SELECTING_SERVICE_ACTION: service_answer_save_callback,
    SELECTING_PROFILE_ACTION: profile_answer_save_callback,
    SELECTING_POLL_ACTION: poll_answer_save_callback
}


async def start_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if update.message.chat.type != "private":
        return END
    payload = context.args[0] if context.args else None
    user_id = update.message.from_user.id
    user = await users_service.get_user(user_id)
    if user is None:
        user = User(user_id, update.message.from_user.username, None)
        user = await users_service.create_user(user)
    last_name = user.last_name if user.last_name else None
    first_name = user.first_name if user.first_name else None
    middle_name = user.middle_name if user.middle_name else None
    object = user.object if user.object else ""
    legal_entity = user.legal_entity if user.legal_entity else ""
    context.user_data[USER_OBJECT] = object
    context.user_data[USER_LEGAL_ENTITY] = legal_entity

    # NEED TO BE OPTIMIZED
    if last_name and middle_name and first_name:
        context.user_data[USER_NAME] = (
            last_name + " " + first_name + " " + middle_name
        )
    else:
        context.user_data[USER_NAME] = None
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
    name = context.user_data.get(USER_NAME)
    legal_entity = context.user_data.get(USER_LEGAL_ENTITY)
    object = context.user_data.get(USER_OBJECT)
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
                ("polling", SELECTING_POLL_ACTION),
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
    await send_message(update, context, text, keyboard, payload=(message))
    return SELECTING_ACTION


async def start_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SELECTING_SERVICE_ACTION
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    context.user_data[ACTIVE_DIALOG] = service_dialog
    context.user_data[ACTIVE_DIALOG_SEQUENCE_ID] = 0
    context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
    await send_message(
        update,
        context,
        "service_header",
        create_keyboard(
            [
                [("edit", SETTING_DIALOG_ITEM)],
                [("back", SELECTING_ACTION)],
            ]
        ),
        payload=["-", "-", "-"],
    )
    return SETTING_DIALOG_ITEM


async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SELECTING_PROFILE_ACTION
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    name = context.user_data.get(USER_NAME)
    object = context.user_data.get(USER_OBJECT)
    legal_entity = context.user_data.get(USER_LEGAL_ENTITY)
    user_id = get_user_id(update)
    user = await users_service.get_user(user_id)
    if user:
        if name:
            last_name = name.split(" ")[0]
            first_name = (
                name.split(" ")[1] if len(name.split(" ")) > 1 else ""
            )
            middle_name = (
                name.split(" ")[2] if len(name.split(" ")) > 2 else ""
            )
            user.first_name = first_name
            user.last_name = last_name
            user.middle_name = middle_name
            await users_service.update_user(user)
        if object:
            user.object = object
            await users_service.update_user(user)
        if legal_entity:
            user.legal_entity = legal_entity
            await users_service.update_user(user)
        context.user_data[ACTIVE_DIALOG] = profile_dialog
        context.user_data[ACTIVE_DIALOG_SEQUENCE_ID] = 0
        context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
        await send_message(
            update,
            context,
            "profile_header",
            create_keyboard(
                [
                    [("edit", SETTING_DIALOG_ITEM)],
                    [("back", SELECTING_ACTION)],
                ]
            ),
        )
    return SELECTING_PROFILE_ACTION


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    set_buffer_message(update, context)
    buffer = context.user_data.get(FEEDBACK_BUFFER) or "отсутствует"
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
    context.user_data[ACTIVE_INPUT_MODE] = SELECTING_POLL_ACTION
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_ACTION
    context.user_data[ACTIVE_DIALOG] = poll_dialog
    context.user_data[ACTIVE_DIALOG_SEQUENCE_ID] = 0
    context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
    text = "poll_header"
    await send_message(
        update,
        context,
        text,
        create_keyboard(
            [[("start", SETTING_DIALOG_ITEM), ("cancel", SELECTING_ACTION)]]
        ),
    )
    return SETTING_DIALOG_ITEM


async def set_dialog_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    active_input_mode: int = context.user_data.get(ACTIVE_INPUT_MODE)
    keyboard = create_keyboard([[("back", SELECTING_ACTION)]])
    dialog = context.user_data.get(ACTIVE_DIALOG)
    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX)
    active_sequence = sequences.get(active_sequence_id)
    active_questions = [questions[i] for i in active_sequence.questions_ids]
    active_question = active_questions[active_sequence_question_index]
    args = None
    if update.callback_query:
        callback_data = update.callback_query.data.split(":")
        try:
            args = int(callback_data[1]) if len(callback_data) > 1 else None
        except ValueError:
            args = None
    text_input = context.user_data.pop(BUFFER_DIALOG_ANSWER, None)
    image_upload = context.user_data.pop(BUFFER_IMAGE, None)
    print(text_input)
    answer: str | None = None
    if text_input:
        answer = text_input
        context.user_data[BUFFER_DIALOG_ANSWER] = None
    elif image_upload:
        answer = image_upload
        context.user_data[BUFFER_IMAGE] = None
    elif args is not None:
        answer = options.get(args).text
    if answer and _dialog_callbacks.get(active_input_mode):
        await _dialog_callbacks.get(active_input_mode)(
            update,
            context,
            active_sequence.dialog_id,
            active_sequence.id,
            active_question.id,
            args,
            answer,
            0,
        )
    if args is not None or text_input or image_upload:
        index = active_questions.index(active_question)
        selected_option = options.get(args)
        if selected_option and selected_option.sequence_id is not None:
            context.user_data[ACTIVE_DIALOG_SEQUENCE_ID] = (
                selected_option.sequence_id
            )
            context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
        elif index + 1 < len(active_questions):
            context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = index + 1
        elif active_sequence.next_sequence_id is not None:
            context.user_data[ACTIVE_DIALOG_SEQUENCE_ID] = (
                active_sequence.next_sequence_id
            )
            context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = 0
        else:
            if _dialog_callbacks.get(active_input_mode):
                await _dialog_callbacks.get(active_input_mode)(
                    update,
                    context,
                    active_sequence.dialog_id,
                    active_sequence.id,
                    active_question.id,
                    args,
                    answer,
                    1,
                )
            await start_menu(update, context)
            return SELECTING_POLL_ACTION
        active_sequence_id = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_ID)
        active_sequence_question_index = context.user_data.get(
            ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX
        )
        active_sequence = sequences.get(active_sequence_id)
        active_questions = [questions[i] for i in active_sequence.questions_ids]
        if active_sequence_question_index < len(active_questions):
            active_question = active_questions[active_sequence_question_index]
        else:
            active_question = None
    button = ("send", TYPING_DIALOG_ANSWER)
    if active_question.type == 0:
        await set_dialog_answer_select(update, context)
        return SETTING_DIALOG_ITEM
    elif active_question.type == 1:
        button = ("send", TYPING_DIALOG_ANSWER)
    elif active_question.type == 2:
        button = ("send", UPLOADING_DIALOG_ANSWER)
    keyboard = create_keyboard(
        [[button, ("cancel", SETTING_DIALOG_ITEM)]]
    )
    question_text = active_question.text if active_question else "No question data"
    await send_message(update, context, question_text, keyboard)
    return SETTING_DIALOG_ITEM


async def set_dialog_answer_typing( update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dialog = context.user_data.get(ACTIVE_DIALOG)
    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(
        ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX
    )
    active_sequence = sequences.get(active_sequence_id)
    active_question_index = active_sequence.questions_ids[
        active_sequence_question_index
    ]
    active_question = questions.get(active_question_index)
    active_options = [
        options[i] for i in (active_question.options_ids or []) if i in options
    ]
    options_buf = []
    for option in active_options:
        options_buf.append(
            (option.text, str(SETTING_DIALOG_ITEM) + ":" + str(option.id))
        )
    options_buf.append(("cancel", SELECTING_ACTION))
    keyboard = create_keyboard([options_buf])
    await send_message(
        update, context, "multi_dialog_question_text_handler_prompt", keyboard
    )
    if update.callback_query:
        set_buffer_message(update, context)
    return TYPING


async def set_dialog_answer_select( update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dialog = context.user_data.get(ACTIVE_DIALOG)
    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(
        ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX
    )
    active_sequence = sequences.get(active_sequence_id)
    active_question_index = active_sequence.questions_ids[
        active_sequence_question_index
    ]
    active_question = questions.get(active_question_index)
    active_options = [
        options[i] for i in (active_question.options_ids or []) if i in options
    ]
    options_buf = []
    for option in active_options:
        options_buf.append(
            (option.text, str(SETTING_DIALOG_ITEM) + ":" + str(option.id))
        )
    options_buf.append(("cancel", SELECTING_ACTION))
    keyboard = create_keyboard([options_buf])
    await send_message(
        update, context, "multi_dialog_question_text_handler_prompt", keyboard
    )
    if update.callback_query:
        set_buffer_message(update, context)
    return SELECTING


async def set_dialog_answer_upload( update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dialog = context.user_data.get(ACTIVE_DIALOG)
    sequences, questions, options = dialog
    active_sequence_id = context.user_data.get(ACTIVE_DIALOG_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(
        ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX
    )
    active_sequence = sequences.get(active_sequence_id)
    active_question_index = active_sequence.questions_ids[
        active_sequence_question_index
    ]
    active_question = questions.get(active_question_index)
    active_options = [
        options[i] for i in (active_question.options_ids or []) if i in options
    ]
    options_buf = []
    for option in active_options:
        options_buf.append(
            (option.text, str(SETTING_DIALOG_ITEM) + ":" + str(option.id))
        )
    options_buf.append(("cancel", SELECTING_ACTION))
    keyboard = create_keyboard([options_buf])
    await send_message(
        update, context, "multi_dialog_question_text_handler_prompt", keyboard
    )
    if update.callback_query:
        set_buffer_message(update, context)
    return UPLOADING


async def back_multi_dialog_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_index = context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX]
    question_index -= 1
    if question_index < 0:
        question_index = 0
        return SETTING_DIALOG_ITEM
    context.user_data[ACTIVE_DIALOG_SEQUENCE_QUESTION_INDEX] = question_index
    await set_dialog_item(update, context)
    return SETTING_DIALOG_ITEM


async def set_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SELECTING_FEEDBACK_ACTION
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    keyboard = create_keyboard([[("cancel", CANCELING)]])
    await send_message(update, context, "feedback_text_handler_prompt", keyboard)
    set_buffer_message(update, context)
    return TYPING


async def send_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    buffer = context.user_data.get(FEEDBACK_BUFFER) or None
    text = None
    if (
        context.user_data.get(USER_NAME) is None
        or context.user_data.get(USER_LEGAL_ENTITY) is None
        or context.user_data.get(USER_OBJECT) is None
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
        context.user_data[FEEDBACK_BUFFER] = None
    else:
        text = "feedback_data_error"
    keyboard = create_keyboard([[("cancel", SELECTING_FEEDBACK_ACTION)]])
    await send_message(update, context, text, keyboard)
    return SELECTING_FEEDBACK_ACTION


async def send_service_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    description = context.user_data.get(SERVICE_DESCRIPTION) or None
    location = context.user_data.get(SERVICE_LOCATION) or None
    image = context.user_data.get(SERVICE_IMAGE) or None
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
        context.user_data.get(USER_NAME) is None
        or context.user_data.get(USER_LEGAL_ENTITY) is None
        or context.user_data.get(USER_OBJECT) is None
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
    context.user_data[SERVICE_DESCRIPTION] = None
    context.user_data[SERVICE_LOCATION] = None
    context.user_data[SERVICE_IMAGE] = None
    return SELECTING_SERVICE_ACTION


def validate_user_data(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data is not None


def validate_message(update: Update) -> bool:
    return update.message is not None


def validate_callback_query(update: Update) -> bool:
    return update.callback_query is not None


async def handle_text_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | str:
    if not validate_user_data(context):
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_SERVICE_ACTION
    if not validate_message(update):
        await send_message(update, context, "message_data_validation_error")
        return SELECTING_SERVICE_ACTION
    user_text = update.message.text.strip()
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    print(active_input_mode)
    if active_input_mode in _text_handler_routes_map:
        context.user_data[_text_handler_routes_map[active_input_mode]] = user_text

    await delete_buffer_message(update, context)
    if active_input_mode in _feedback_input_modes:
        await start_feedback(update, context)
        return SELECTING_FEEDBACK_ACTION
    else:
        await set_dialog_item(update, context)
        return SETTING_DIALOG_ITEM
    return SELECTING_ACTION


async def handle_image_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_buffer_message(update, context)
    photo_file = await update.message.photo[-1].get_file()
    logger.info(f"Image received and stored with file_id: {photo_file.file_id}")
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    if active_input_mode in _image_handler_routes_map:
        context.user_data[_image_handler_routes_map[active_input_mode]] = photo_file.file_id
    await delete_buffer_message(update, context)
    if active_input_mode in _feedback_input_modes:
        await start_feedback(update, context)
        return SELECTING_FEEDBACK_ACTION
    else:
        await set_dialog_item(update, context)
        return SETTING_DIALOG_ITEM
    return SELECTING_SERVICE_ACTION


async def cancel_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
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
            return SELECTING_POLL_ACTION
        if active_input_mode in _feedback_input_modes:
            await start_feedback(update, context)
            return SELECTING_FEEDBACK_ACTION


async def clear_text_buffer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if context.user_data is None:
        await send_message(update, context, "user_data_validation_error")
        return SELECTING_ACTION
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    if active_input_mode:
        context.user_data[_text_handler_routes_map[active_input_mode]] = None
    await send_message(update, context, "Canceled")
    if active_input_mode in _service_input_modes:
        await start_service(update, context)
        return SELECTING_SERVICE_ACTION
    if active_input_mode in _profile_input_modes:
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION
    if active_input_mode in _polling_input_modes:
        await start_poll(update, context)
        return SELECTING_POLL_ACTION


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the bot with a specified Telegram token."
    )
    parser.add_argument("token", help="The Telegram bot token")

    args = parser.parse_args()
    application = Application.builder().token(args.token).build()
    multi_dialog_states = {
        TYPING: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
        ],
        UPLOADING: [
            MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_image_input)
        ],
        SELECTING_DIALOG_ANSWER: [
            CallbackQueryHandler(
                set_dialog_answer_select,
                pattern="^" + str(SELECTING_DIALOG_ANSWER) + "$",
            )
        ],
        TYPING_DIALOG_ANSWER : [
            CallbackQueryHandler(
                set_dialog_answer_typing,
                pattern="^" + str(TYPING_DIALOG_ANSWER) + "$",
            )
        ],
        UPLOADING_DIALOG_ANSWER : [
            CallbackQueryHandler(
                set_dialog_answer_upload,
                pattern="^" + str(UPLOADING_DIALOG_ANSWER) + "$",
            )
        ],
        SETTING_DIALOG_ITEM: [
            CallbackQueryHandler(
                set_dialog_item,
                pattern="^" + str(SETTING_DIALOG_ITEM) + r":?(\d+)?$",
            )
        ],
    }
    multi_dialog_fallbacks = [
        CallbackQueryHandler(
            set_dialog_answer_select, pattern="^" + str(SELECTING_DIALOG_ANSWER) + "$"
        ),
        CallbackQueryHandler(
            set_dialog_answer_typing, pattern="^" + str(TYPING_DIALOG_ANSWER) + "$"
        ),
        CallbackQueryHandler(
            set_dialog_answer_upload, pattern="^" + str(UPLOADING_DIALOG_ANSWER) + "$"
        ),
        CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
        CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
        CallbackQueryHandler(back_multi_dialog_item, pattern = "^" + str(CANCELING_DIALOG_ITEM)+ "$"),
        CallbackQueryHandler(
            set_dialog_item,
            pattern="^" + str(SETTING_DIALOG_ITEM) + r":?(\d+)?$",
        ),
    ]
    service_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_service, pattern="^" + str(SELECTING_SERVICE_ACTION) + "$"
            )
        ],
        states=multi_dialog_states,
        fallbacks=multi_dialog_fallbacks,
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    profile_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_profile, pattern="^" + str(SELECTING_PROFILE_ACTION) + "$"
            )
        ],
        states=multi_dialog_states,
        fallbacks=multi_dialog_fallbacks,
        map_to_parent={SELECTING_ACTION: SELECTING_ACTION},
    )
    polling_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_poll, pattern="^" + str(SELECTING_POLL_ACTION) + "$"
            )
        ],
        states=multi_dialog_states,
        fallbacks=multi_dialog_fallbacks,
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

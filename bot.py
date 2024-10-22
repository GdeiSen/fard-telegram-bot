import logging
import datetime
import argparse
from objects import Feedback, Poll, Answer, Option, Sequence, Question, ServiceTicket, User
from services import FeedbacksService, PollService, ServicesService, UsersService
from database import Database
from utils.poll_json_converter import json_to_sequences
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
json_file = './poll.json'
poll = json_to_sequences(json_file)
db = Database('database.db')
db.create_tables()
feedbacksService = FeedbacksService(db)
servicesService = ServicesService(db)
pollService = PollService(db)
usersService = UsersService(db)


def get_user_id(update: Update) -> int:
    try:
        return update.message.from_user.id
    except Exception as e:
        return update.callback_query.from_user.id
    

def set_buffer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message:
            context.user_data[BUFFER_MESSAGE] = (update.message)
        elif update.callback_query:
            context.user_data[BUFFER_MESSAGE] = (update.callback_query.message)
    except Exception as e:
        print(e)


async def delete_buffer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_td = context.user_data.get(BUFFER_MESSAGE)
    try:
        await context.bot.delete_message(chat_id=message_td.chat_id, message_id=message_td.message_id)
    except Exception as e:
        try:
            await context.bot.delete_message(chat_id=message_td.chat_id, message_id=message_td.message_id)
        except Exception as e:
            print(e)
            pass
    context.user_data[BUFFER_MESSAGE] = []


async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup | None = None, new_message: bool = False) -> None:
    try:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        try:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            try:
                await context.bot.send_message(update.message.chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception as e:
                await context.bot.send_message(update.callback_query.message.chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


LPR_ROLE = 10011
MA_ROLE = 20122

SELECTING_ACTION = 1
(
    SELECTING_SERVICE_ACTION, 
    SELECTING_PROFILE_ACTION, 
    SELECTING_POLLING_ACTION,
    SELECTING_FEEDBACK_ACTION
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

(
    TYPING, 
    UPLOADING, 
    CANCELING, 
    CLEARING
) = range(300, 304)

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
    BUFFER_POLL_ANSWER, 
    BUFFER_QUESTION_MESSAGE, 
    ACTIVE_POLL_SEQUENCE_ID, 
    ACTIVE_POLL_SEQUENCE_QUESTION_INDEX, 
    ACTIVE_POLL, 
    BUFFER_FEEDBACK, 
    BUFFER_POLL_ANSWERS,
    FIRST_START,
    STATUS
) = range(400, 419)

_constates_map = {
        SETTING_SERVICE_DESCRIPTION: BUFFER_DESCRIPTION,
        SETTING_SERVICE_DESCRIPTION_LOCATION: BUFFER_LOCATION,
        SETTING_PROFILE_OBJECT: BUFFER_OBJECT,
        SETTING_PROFILE_NAME: BUFFER_NAME,
        SETTING_PROFILE_LEGAL_ENTITY: BUFFER_LEGAL_ENTITY,
        SETTING_POLL_QUESTION: BUFFER_POLL_ANSWER,
        SETTING_FEEDBACK: BUFFER_FEEDBACK,
        UPLOADING: BUFFER_IMAGE,
        SETTING_SERVICE_DESCRIPTION_IMAGE: BUFFER_IMAGE
}
_service_input_modes = [SETTING_SERVICE_DESCRIPTION, 
                        SETTING_SERVICE_DESCRIPTION_LOCATION, 
                        SETTING_SERVICE_DESCRIPTION_IMAGE]
_profile_input_modes = [SETTING_PROFILE_NAME, 
                        SETTING_PROFILE_OBJECT, 
                        SETTING_PROFILE_LEGAL_ENTITY]
_polling_input_modes = [SETTING_POLL_QUESTION, 
                        SENDING_POLL_ANSWER]
_feedback_input_modes = [SETTING_FEEDBACK]



async def start_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if update.message.chat.type != 'private':
        return END
    
    payload = context.args[0] if context.args else None
    user_id = update.message.from_user.id
    user = await usersService.get_user(user_id)
    context.user_data[BUFFER_POLL_ANSWERS] = []
    
    if user is None:
        user = User(user_id, update.message.from_user.username, None)
        user = await usersService.create_user(user)

    last_name = user.last_name if user.last_name else None
    first_name = user.first_name if user.first_name else None
    middle_name = user.middle_name if user.middle_name else None
    username = user.username if user.username else ""
    object = user.object if user.object else ""
    legal_entity = user.legal_entity if user.legal_entity else ""
    context.user_data[BUFFER_OBJECT] = object
    context.user_data[BUFFER_LEGAL_ENTITY] = legal_entity
    
    # NEED TO BE OPTIMIZED
    if last_name and middle_name and first_name: 
        context.user_data[BUFFER_NAME] = last_name + " " + first_name + " " + middle_name
    else:
        context.user_data[BUFFER_NAME] = None
    #
        
    keyboard = [
        [
            InlineKeyboardButton("Продолжить", callback_data=SELECTING_ACTION)
        ]
    ]
    try:
        context.user_data[FIRST_START]
    except KeyError:
        context.user_data[FIRST_START] = True
        
    if context.user_data[FIRST_START]:    
        if payload == str(LPR_ROLE):
            user.role = LPR_ROLE
            await send_message(update, context, "✅ Ваш тип профиля успешно идентифицирован.")
        elif payload == str(MA_ROLE):
            user.role = MA_ROLE
            await send_message(update, context, "✅ Ваш тип профиля успешно идентифицирован.")
        else:
            await send_message(update, context, "⚠️ Идентификация типа профиля не удалась. Пожалуйста, попробуйте еще раз.\n\nИспользуется демонстрационный режим")
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data=SELECTING_ACTION)
            ]
        ]
        
        await usersService.update_user(user)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send_message(update, context, "❗ Вы даете согласие на обработку ваших персональных данных?", reply_markup)
        context.user_data[FIRST_START] = False
        return SELECTING_ACTION
        
    else:
        await send_message(update, context, "✅ Данные синхронизированы! \n\nС возвращением!\nПриступить к работе?", InlineKeyboardMarkup(keyboard))
        return SELECTING_ACTION


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data.get(BUFFER_NAME)
    legal_entity = context.user_data.get(BUFFER_LEGAL_ENTITY)
    object = context.user_data.get(BUFFER_OBJECT)
    first_name = (" " + name.split(' ')[1]) if name else ""
    middle_name = name.split(' ')[2] if name else ""
    user_id = get_user_id(update)
    user = await usersService.get_user(user_id)
    if not name:
        message = "\n\n<b>⚠️ Требуется действие!</b>\n<i>Для начала использования бота, пожалуйста, укажите свои личную информацию в профиле.</i>"
    elif not legal_entity:
        message = "\n\n<b>⚠️ Требуется действие!</b>\n<i>Для начала использования бота, пожалуйста, укажите свою юридическую информацию в профиле.</i>"
    elif not object:
        message = "\n\n<b>⚠️ Требуется действие!</b>\n<i>Для начала использования бота, пожалуйста, укажите на каком объекте вы арендуете площадь в профиле.</i>"
    else:
        message = ""
    keyboard = [
        [
            InlineKeyboardButton("Профиль" if message == "" else "⚠️ Профиль", callback_data=SELECTING_PROFILE_ACTION),
            InlineKeyboardButton("Обслуживание", callback_data=SELECTING_SERVICE_ACTION),
        ],
        [
            InlineKeyboardButton("Опрос", callback_data=SELECTING_POLLING_ACTION),
            InlineKeyboardButton("Обратная связь", callback_data=SELECTING_FEEDBACK_ACTION),
        ]
    ]
    text = "<b>👋 Здравствуйте" + first_name + " " + middle_name + "! </b>\n" + "Вас приветствует чат-бот управляющей компании Фард Сити" + message + "\n\n<b>📌 Этот бот обладает рядом функций:</b>\n<b>1. Обслуживание.</b> Через диалог с ботом вы можете подать заявку наобслуживание и ремонт. \n<b>2. Опрос.</b> В этом разделе вы можете пройти опрос, который позволит улучшить нам качество управления и обслуживания Норд Сити \n<b>3. Обратная связь.</b> Если у вас есть какие-то идеи или предложения о том, как улучшить Норд Сити, оставляйте их здесь.\n<b>4. Профиль.</b> С помощью меню вы можете изменить свою личную информацию \n\n<b>Выберите действие:</b>"
    if user.role == MA_ROLE:
        text = "<b>👋 Здравствуйте" + first_name + " " + middle_name + "! </b>\n" + "Вас приветствует чат-бот управляющей компании Фард Сити" + message + "\n\n<b>📌 Этот бот обладает рядом доступных для вас функций:</b>\n<b>1. Обслуживание.</b> Через диалог с ботом вы можете подать заявку наобслуживание и ремонт.\n<b>2. Профиль.</b> С помощью меню вы можете изменить свою личную информацию \n\n<b>Выберите действие:</b>"
        keyboard = [
        [
            InlineKeyboardButton("Профиль" if message == "" else "⚠️ Профиль", callback_data=SELECTING_PROFILE_ACTION),
            InlineKeyboardButton("Обслуживание", callback_data=SELECTING_SERVICE_ACTION),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, text, reply_markup)
    return SELECTING_ACTION


async def start_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("+ Описание", callback_data=SETTING_SERVICE_DESCRIPTION),
            InlineKeyboardButton("+ Местоположение", callback_data=SETTING_SERVICE_DESCRIPTION_LOCATION),
            InlineKeyboardButton("+ Изображение", callback_data=SETTING_SERVICE_DESCRIPTION_IMAGE)
        ],
        [InlineKeyboardButton("Назад", callback_data=SELECTING_ACTION), InlineKeyboardButton("Отправить", callback_data=SENDING_SERVICE)]
    ]
    current_problem = context.user_data.get(BUFFER_DESCRIPTION) or "не указано"
    current_location = context.user_data.get(BUFFER_LOCATION) or "не указано"
    current_image = "не прикреплено"
    if context.user_data.get(BUFFER_IMAGE):
        current_image = "прикреплено"
    text = f"🚩 <b>Текущий тикет</b> \n\n<b>Описание:</b>\n<i>{current_problem}</i>\n\n<b>Местоположение:</b>\n<i>{current_location}</i>\n\n<b>Изображение:</b>\n<i>{current_image}</i>"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, text, reply_markup)
    return SELECTING_SERVICE_ACTION


async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("+ Имя", callback_data=SETTING_PROFILE_NAME),
            InlineKeyboardButton("+ Юр. Лицо", callback_data=SETTING_PROFILE_LEGAL_ENTITY),
            InlineKeyboardButton("+ Объект", callback_data=SETTING_PROFILE_OBJECT)
        ],
        [InlineKeyboardButton("Назад", callback_data=SELECTING_ACTION)]
    ]
    buffer_name = context.user_data.get(BUFFER_NAME)
    buffer_object = context.user_data.get(BUFFER_OBJECT)
    buffer_legal_entity = context.user_data.get(BUFFER_LEGAL_ENTITY)
    user_id = get_user_id(update)
    user = await usersService.get_user(user_id)
    if user:
        if buffer_name:
            last_name = buffer_name.split(' ')[0]
            first_name = buffer_name.split(' ')[1] if len(buffer_name.split(' ')) > 1 else ""
            middle_name = buffer_name.split(' ')[2] if len(buffer_name.split(' ')) > 2 else ""
            user.first_name = first_name
            user.last_name = last_name
            user.middle_name = middle_name
            await usersService.update_user(user)
        if buffer_object:
            object = buffer_object
            user.object = object
            await usersService.update_user(user)
        if buffer_legal_entity:
            legal_entity = buffer_legal_entity
            user.legal_entity = legal_entity
            await usersService.update_user(user)

    text = f"👤 <b>Ваш профиль</b>\nЗдесь указана ваша личная информация необходимая для идентификации \n\n<b>Имя:</b>\n<i>{buffer_name or 'не указано'}</i>\n\n<b>Юридическое лицо:</b>\n<i>{buffer_legal_entity or 'не указано'}</i>\n\n<b>Объект</b>\n<i>{buffer_object or 'не указано'}</i>"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, text, reply_markup)
    return SELECTING_PROFILE_ACTION


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_buffer_message(update, context)
    keyboard = [
        [InlineKeyboardButton("Изменить", callback_data=SETTING_FEEDBACK)],
        [InlineKeyboardButton("Отправить", callback_data=SENDING_FEEDBACK)],
        [InlineKeyboardButton("Отмена", callback_data=SELECTING_ACTION)]
    ]
    buffer = context.user_data.get(BUFFER_FEEDBACK) or "отсутствует"
    text = f"🚩 <b>Обратная связь</b>\nВы можете отправить отзыв в администрацию Фард Сити, чтобы мы могли понять, как нам стать лучше\n\n<b>Текущий буфер:</b>\n<i>{buffer}</i>"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, text, reply_markup)
    return SELECTING_FEEDBACK_ACTION


async def start_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data=SETTING_POLL_QUESTION)],
        [InlineKeyboardButton("Отмена", callback_data=SELECTING_ACTION)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data[ACTIVE_POLL] = poll
    context.user_data[ACTIVE_POLL_SEQUENCE_ID] = 0
    context.user_data[ACTIVE_POLL_SEQUENCE_QUESTION_INDEX] = 0
    text = "📊 <b>Опрос</b>\nПожалуйста, поделитесь с нами, что мы можем улучшить или изменить в Норд Сити, для того чтобы это место стало лучше для вас.\n\nНачать опрос?"
    await send_message(update, context, text, reply_markup)
    return SETTING_POLL_QUESTION


async def set_poll_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=SELECTING_ACTION)]
    ]
    
    if context.user_data.get(BUFFER_NAME) is None or context.user_data.get(BUFFER_LEGAL_ENTITY) is None or context.user_data.get(BUFFER_OBJECT) is None:
        await send_message(update, context, "⚠️ Пожалуйста заполните свой профиль для взаимодействия с ботом!", InlineKeyboardMarkup(keyboard))
        return SELECTING_POLLING_ACTION
    
    poll = context.user_data.get(ACTIVE_POLL)
    if poll is None:
        await send_message(update, context, "⚠️ Вариант опроса не был выбран")
        return SELECTING_ACTION

    sequences, questions, options = poll
    active_sequence_id = context.user_data.get(ACTIVE_POLL_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(ACTIVE_POLL_SEQUENCE_QUESTION_INDEX)
    
    if active_sequence_id is None or active_sequence_question_index is None:
        await send_message(update, context, "⚠️ Ошибка в данных опроса.")
        return SELECTING_ACTION
    
    active_sequence = sequences.get(active_sequence_id)
    if not active_sequence or not active_sequence.questions_ids:
        await send_message(update, context, "⚠️ Ошибка в вопросах последовательности.")
        return SELECTING_ACTION

    active_questions = [questions[i] for i in active_sequence.questions_ids]
    if active_sequence_question_index >= len(active_questions):
        await send_message(update, context, "⚠️ Вопрос из текущей последовательности отсутствует.")
        return SELECTING_ACTION

    active_question = active_questions[active_sequence_question_index]
    
    args = None
    if update.callback_query:
        callback_data = update.callback_query.data.split(':')
        try:
            args = int(callback_data[1]) if len(callback_data) > 1 else None
        except ValueError:
            args = None

    text_input = context.user_data.pop(BUFFER_POLL_ANSWER, None)
    answer = None
    if text_input:
        answer = text_input
        context.user_data[BUFFER_POLL_ANSWER] = None
    elif args:
        answer = options.get(args).text
    if answer:
        answer_question = Question(
        id=active_question.id,
        text=active_question.text,
        options_ids=active_question.options_ids
        )
        answer_question.answer = answer
        context.user_data[BUFFER_POLL_ANSWERS].append(answer_question)
    
    if args is not None or text_input:
        index = active_questions.index(active_question)
        selected_option = options.get(args)
        
        if selected_option and selected_option.sequence_id is not None:
            context.user_data[ACTIVE_POLL_SEQUENCE_ID] = selected_option.sequence_id
            context.user_data[ACTIVE_POLL_SEQUENCE_QUESTION_INDEX] = 0
        elif index + 1 < len(active_questions):
            context.user_data[ACTIVE_POLL_SEQUENCE_QUESTION_INDEX] = index + 1
        elif active_sequence.next_sequence_id is not None:
            context.user_data[ACTIVE_POLL_SEQUENCE_ID] = active_sequence.next_sequence_id
            context.user_data[ACTIVE_POLL_SEQUENCE_QUESTION_INDEX] = 0
        else:
            await send_message(update, context, "✅ Опрос завершен")

            await start_poll(update, context)
            return SELECTING_POLLING_ACTION

        active_sequence_id = context.user_data.get(ACTIVE_POLL_SEQUENCE_ID)
        active_sequence_question_index = context.user_data.get(ACTIVE_POLL_SEQUENCE_QUESTION_INDEX)
        
        active_sequence = sequences.get(active_sequence_id)
        if not active_sequence:
            await send_message(update, context, "⚠️ Ошибка в следующих этапах последовательности.")
            return SELECTING_ACTION

        active_questions = [questions[i] for i in active_sequence.questions_ids]
        if active_sequence_question_index < len(active_questions):
            active_question = active_questions[active_sequence_question_index]
        else:
            active_question = None
    
    keyboard = [
        [InlineKeyboardButton("Ответить", callback_data=SENDING_POLL_ANSWER)],
        [InlineKeyboardButton("Отмена", callback_data=SELECTING_ACTION)]
    ]

    question_text = active_question.text if active_question else "No question data"
    try:
        await update.callback_query.edit_message_text(question_text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await update.message.reply_text(question_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SETTING_POLL_QUESTION



async def set_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_POLL_QUESTION
    poll = context.user_data.get(ACTIVE_POLL)

    if poll is None:
        await send_message(update, context, "⚠️ Опрос не найден.")
        return SELECTING_ACTION

    sequences, questions, options = poll
    active_sequence_id = context.user_data.get(ACTIVE_POLL_SEQUENCE_ID)
    active_sequence_question_index = context.user_data.get(ACTIVE_POLL_SEQUENCE_QUESTION_INDEX)

    if active_sequence_id is None or active_sequence_question_index is None:
        await send_message(update, context, "⚠️ Активные индексы последовательности и вопроса не заданы.")
        return SELECTING_ACTION

    active_sequence = sequences.get(active_sequence_id)
    if not active_sequence or not active_sequence.questions_ids:
        await send_message(update, context, "⚠️ Ошибка в данных последовательности.")
        return SELECTING_ACTION

    if active_sequence_question_index >= len(active_sequence.questions_ids):
        await send_message(update, context, "⚠️ Вопросов нет в текущей последовательности.")
        return SELECTING_ACTION

    active_question_index = active_sequence.questions_ids[active_sequence_question_index]
    active_question = questions.get(active_question_index)

    if active_question is None:
        await send_message(update, context, "⚠️ Ошибка в данных вопроса.")
        return SELECTING_ACTION

    active_options = [options[i] for i in (active_question.options_ids or []) if i in options]

    keyboard = [
        [InlineKeyboardButton(option.text, callback_data=f"{SETTING_POLL_QUESTION}:{option.id}")]
        for option in active_options
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data=SELECTING_ACTION)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Введите ответ на вопрос:", reply_markup)

    if update.callback_query:
        set_buffer_message(update, context)

    return TYPING


async def set_profile_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_NAME
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)], [InlineKeyboardButton("Стереть", callback_data=CLEARING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Укажите свое имя\n\nПример: Иванов Иван Иванович", reply_markup)
    set_buffer_message(update, context)
    return TYPING


async def set_profile_legal_entity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_LEGAL_ENTITY
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)], [InlineKeyboardButton("Стереть", callback_data=CLEARING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Укажите юридическое лицо\n\nПример: МТБ-Банк", reply_markup)
    set_buffer_message(update, context)
    return TYPING


async def set_profile_object(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_PROFILE_OBJECT
    args = update.callback_query.data.split(':')
    args = args[1] if len(args) > 1 else None
    if args:
        if args == '1':
            context.user_data[BUFFER_OBJECT] = "БЦ 'Основателей'"
        elif args == '2':
            context.user_data[BUFFER_OBJECT] = "МФК 'Нордсити'"
        elif args == '3':
            context.user_data[BUFFER_OBJECT] = "Стелла"
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION
    keyboard = [
        [InlineKeyboardButton("БЦ 'Основателей'", callback_data=str(SETTING_PROFILE_OBJECT)+':1')],
        [InlineKeyboardButton("МФК 'Нордсити'", callback_data=str(SETTING_PROFILE_OBJECT)+':2')],
        [InlineKeyboardButton("Стелла", callback_data=str(SETTING_PROFILE_OBJECT)+':3')],
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)]
    ]
    set_buffer_message(update, context)
    await update.callback_query.edit_message_text("Выберите объект:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_PROFILE_ACTION


async def set_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_FEEDBACK
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Напишите ваше предложение:", reply_markup)
    set_buffer_message(update, context)
    return TYPING

async def send_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buffer = context.user_data.get(BUFFER_FEEDBACK) or None
    text = None
    if context.user_data.get(BUFFER_NAME) is None or context.user_data.get(BUFFER_LEGAL_ENTITY) is None or context.user_data.get(BUFFER_OBJECT) is None:
        text = "⚠️ Пожалуйста, заполните свой профиль для отправки отзыва"
    elif buffer:
        feedback = await feedbacksService.create_feedback(Feedback(0, user_id=get_user_id(update), text=buffer, created_at=datetime.datetime.now()))
        text = "✅ Отзыв отправлен!\nВаше мнение очень важно для нас!"
        context.user_data[BUFFER_FEEDBACK] = None
    else:
        text = "⚠️ Пожалуйста, напишите отзыв для отправки"
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=SELECTING_FEEDBACK_ACTION)]
    ]
    await send_message(update, context, text, InlineKeyboardMarkup(keyboard), new_message=True)
    return SELECTING_FEEDBACK_ACTION


async def set_service_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)], [InlineKeyboardButton("Стереть", callback_data=CLEARING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Опишите возникшую проблему:", reply_markup)
    set_buffer_message(update, context)
    return TYPING


async def set_service_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION_LOCATION
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)], [InlineKeyboardButton("Стереть", callback_data=CLEARING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Укажите расположение возникшей проблемы:", reply_markup)
    set_buffer_message(update, context)
    return TYPING


async def set_service_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[ACTIVE_INPUT_MODE] = SETTING_SERVICE_DESCRIPTION_IMAGE
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data=CANCELING)], [InlineKeyboardButton("Стереть", callback_data=CLEARING)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, "✏️ Отправьте изображение проблемы:", reply_markup)
    set_buffer_message(update, context)
    return UPLOADING


async def send_service_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = context.user_data.get(BUFFER_DESCRIPTION) or None
    location = context.user_data.get(BUFFER_LOCATION) or None
    image = context.user_data.get(BUFFER_IMAGE) or None
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=SELECTING_SERVICE_ACTION)]
    ]
    if description is None or location is None:
        await send_message(update, context, "⚠️ Описание и местоположение проблемы не указаны", InlineKeyboardMarkup(keyboard))
        return SELECTING_SERVICE_ACTION
    elif context.user_data.get(BUFFER_NAME) is None or context.user_data.get(BUFFER_LEGAL_ENTITY) is None or context.user_data.get(BUFFER_OBJECT) is None:
        await send_message(update, context, "⚠️ Пожалуйста заполните свой профиль для взаимодействия с ботом!", InlineKeyboardMarkup(keyboard))
        return SELECTING_SERVICE_ACTION
    service_ticket = await servicesService.create_service_ticket(ServiceTicket(0, user_id=get_user_id(update), description=description, location=location, image=image, checked=False))
    await send_message(update, context, "✅ Ваш тикет отправлен!\nМы учтем вашу проблему и займемся ее решением!", InlineKeyboardMarkup(keyboard))
    context.user_data[BUFFER_DESCRIPTION] = None
    context.user_data[BUFFER_LOCATION] = None
    context.user_data[BUFFER_IMAGE] = None
    return SELECTING_SERVICE_ACTION


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | str:
    user_text = update.message.text.strip()
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)

    if active_input_mode in _constates_map:
        context.user_data[_constates_map[active_input_mode]] = user_text

    await delete_buffer_message(update, context)

    if active_input_mode in _service_input_modes:
        if not validate_service_location(context):
            await send_message(update, context, "⚠️ Местоположение проблемы не должно превышать 1000 символов.")
            context.user_data[BUFFER_LOCATION] = None
        elif not validate_service_description(context):
            await send_message(update, context, "⚠️ Описание проблемы не должно превышать 1000 символов.")
            context.user_data[BUFFER_DESCRIPTION] = None
        await start_service(update, context)
        return SELECTING_SERVICE_ACTION

    elif active_input_mode in _profile_input_modes:
        if not validate_profile_object(context):
            await send_message(update, context, "⚠️ Объект должен быть не более 1000 символов.")
            context.user_data[BUFFER_OBJECT] = None
        elif not validate_profile_name(context):
            await send_message(update, context, "⚠️ Имя должно быть в формате: Фамилия Имя Отчество\nИли фамилия должна быть не менее 3-х символов, и общее количество не более 50 символов.")
            context.user_data[BUFFER_NAME] = None
        await start_profile(update, context)
        return SELECTING_PROFILE_ACTION

    elif active_input_mode in _polling_input_modes:
        if not validate_question_text(context):
            await send_message(update, context, "⚠️ Ответ на вопрос не должен превышать 1000 символов.")
            context.user_data[BUFFER_POLL_ANSWER] = None
        await set_poll_question(update, context)
        return SETTING_POLL_QUESTION

    elif active_input_mode in _feedback_input_modes:
        await start_feedback(update, context)
        return SELECTING_FEEDBACK_ACTION

    context.user_data[ACTIVE_INPUT_MODE] = None
    return SELECTING_ACTION


def validate_question_text(context: ContextTypes.DEFAULT_TYPE) -> bool:
    question_text = context.user_data.get(BUFFER_POLL_ANSWER, '')
    return question_text is None or len(question_text) <= 1000


def validate_service_description(context: ContextTypes.DEFAULT_TYPE) -> bool:
    description = context.user_data.get(BUFFER_DESCRIPTION, '')
    return description is None or len(description) <= 1000


def validate_service_location(context: ContextTypes.DEFAULT_TYPE) -> bool:
    location = context.user_data.get(BUFFER_LOCATION, '')
    return location is None or len(location) <= 1000 


def validate_profile_object(context: ContextTypes.DEFAULT_TYPE) -> bool:
    profile_object = context.user_data.get(BUFFER_OBJECT, '')
    return profile_object is None or len(profile_object) <= 1000


def validate_profile_name(context: ContextTypes.DEFAULT_TYPE) -> bool:
    buffer_name = context.user_data.get(BUFFER_NAME, '')
    if not buffer_name:
        return False
    parts = buffer_name.split(' ')
    return len(parts) == 3 and len(parts[0]) >= 3 and sum(len(part) for part in parts) <= 50



async def handle_image_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        await delete_buffer_message(update, context)
        photo_file = await update.message.photo[-1].get_file()
        context.user_data[BUFFER_IMAGE] = photo_file.file_id
        logger.info(f"Image received and stored with file_id: {photo_file.file_id}")
    except (IndexError, AttributeError) as e:
        logger.error(f"Failed to process image input: {e}")
        await update.message.reply_text("Не удалось обработать изображение. Пожалуйста, попробуйте еще раз.")
        return SELECTING_SERVICE_ACTION

    await start_service(update, context)
    return SELECTING_SERVICE_ACTION


async def cancel_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int|None:
    await update.callback_query.edit_message_text("Отменено")
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


async def clear_text_buffer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int|None:
    active_input_mode = context.user_data.get(ACTIVE_INPUT_MODE)
    if active_input_mode:
        context.user_data[_constates_map[active_input_mode]] = None
    await update.callback_query.edit_message_text("Удалено")
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
    parser = argparse.ArgumentParser(description="Run the bot with a specified Telegram token.")
    parser.add_argument("token", help="The Telegram bot token")

    args = parser.parse_args()
    application = Application.builder().token(args.token).build()
    service_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_service, pattern="^" + str(SELECTING_SERVICE_ACTION) + "$")],
        states={
            UPLOADING: [MessageHandler(filters.PHOTO, handle_image_input)],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            SELECTING_SERVICE_ACTION: [
                CallbackQueryHandler(set_service_description, pattern="^" + str(SETTING_SERVICE_DESCRIPTION) + "$"),
                CallbackQueryHandler(set_service_location, pattern="^" + str(SETTING_SERVICE_DESCRIPTION_LOCATION) + "$"),
                CallbackQueryHandler(set_service_image, pattern="^" + str(SETTING_SERVICE_DESCRIPTION_IMAGE) + "$"),
                CallbackQueryHandler(send_service_ticket, pattern="^" + str(SENDING_SERVICE) + "$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(start_service, pattern="^" + str(SELECTING_SERVICE_ACTION) + "$")
        ],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION
        }
    )
    profile_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_profile, pattern="^" + str(SELECTING_PROFILE_ACTION) + "$")],
        states={
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            SELECTING_PROFILE_ACTION: [
                CallbackQueryHandler(set_profile_name, pattern="^" + str(SETTING_PROFILE_NAME) + "$"),
                CallbackQueryHandler(set_profile_legal_entity, pattern="^" + str(SETTING_PROFILE_LEGAL_ENTITY) + "$"),
                CallbackQueryHandler(set_profile_object, pattern="^" + str(SETTING_PROFILE_OBJECT) + r":?(\d+)?$"),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(start_service, pattern="^" + str(SELECTING_PROFILE_ACTION) + "$")
        ],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION
        }
    )

    polling_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_poll, pattern="^" + str(SELECTING_POLLING_ACTION) + "$")],
        states={
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            SENDING_POLL_ANSWER: [CallbackQueryHandler(set_poll_answer, pattern="^" + str(SENDING_POLL_ANSWER) + "$")],
            SETTING_POLL_QUESTION: [CallbackQueryHandler(set_poll_question, pattern="^" + str(SETTING_POLL_QUESTION) + r":?(\d+)?$")]
        },
        fallbacks=[
            CallbackQueryHandler(set_poll_answer, pattern="^" + str(SENDING_POLL_ANSWER) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(set_poll_question, pattern="^" + str(SETTING_POLL_QUESTION) + r":?(\d+)?$")
        ],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION
        }
    )

    feedback_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_feedback, pattern="^" + str(SELECTING_FEEDBACK_ACTION) + "$")],
        states={
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            SELECTING_FEEDBACK_ACTION: [
                CallbackQueryHandler(set_feedback, pattern="^" + str(SETTING_FEEDBACK) + "$"),
                CallbackQueryHandler(send_feedback, pattern="^" + str(SENDING_FEEDBACK) + "$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(clear_text_buffer, pattern="^" + str(CLEARING) + "$"),
            CallbackQueryHandler(cancel_text_input, pattern="^" + str(CANCELING) + "$"),
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"),
            CallbackQueryHandler(start_feedback, pattern="^" + str(SELECTING_FEEDBACK_ACTION) + "$")
        ],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION
        }
    )

    main_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$"), CommandHandler("menu", start_menu)],
        states={
            SELECTING_ACTION: [
                profile_conv_handler,
                service_conv_handler,
                polling_conv_handler,
                feedback_conv_handler
            ]
        },
        fallbacks=[
            CallbackQueryHandler(start_menu, pattern="^" + str(SELECTING_ACTION) + "$")
        ]
    )
    application.add_handler(main_conv_handler)
    application.add_handler(CommandHandler("start", start_app))
    application.add_handler(CommandHandler("menu", start_menu))
    application.run_polling()

if __name__ == "__main__":
    main()

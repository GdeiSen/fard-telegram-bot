from typing import Dict

Data: Dict[str, dict] = {
    "RU": {
        # ::buttons
        'continue': "Продолжить",
        'back': "Назад",
        'clear': "Стереть",
        'edit': "Изменить",
        'start': "Начать",
        'answer': "Ответить",
        'cancel': "Отмена",
        'send': "Отправить",
        'agree': "Даю согласие",
        'profile': 'Профиль',
        'profile_warn': '⚠️ Профиль',
        'service': 'Обслуживание',
        'polling': 'Опрос',
        'feedback': 'Обратная связь',
        'description': '+ Описание',
        'location': '+ Местоположение',
        'image': '+ Изображение',
        'name': '+ Имя',
        'legal_entity': '+ Юр. лицо',
        'object': '+ Объект',
        # ::warns
        'user_data_validation_error': '⚠️ Ошибка в данных пользователя.',
        'user_profile_validation_error': '\n\n⚠️ Пожалуйста заполните свой профиль для взаимодействия с ботом!',
        'user_profile_identification_error': '⚠️ Идентификация типа профиля не удалась. Пожалуйста, попробуйте еще раз.\n\nИспользуется демонстрационный режим',
        'message_data_validation_error': '⚠️ Ошибка в данных сообщения.',
        'text_length_validation_error': '⚠️ К сожалению ваш ответ превышает допустимый лимит в 1000 символов. Пожалуйста, укажите более краткий вариант.',
        'multi_dialog_data_error': '⚠️ Ошибка в данных диалога.',
        'profile_action_required_warning': '<b>⚠️ Требуется действие!</b>\n<i>Для начала использования бота, пожалуйста, укажите свои личную информацию в профиле.</i>',
        'feedback_data_error': '⚠️ Пожалуйста сначала напишите отзыв для отправки',
        'service_data_error': '⚠️ Описание и местоположение проблемы не указаны',
        # ::success
        'profile_identification_completed': '✅ Ваш тип профиля успешно идентифицирован.',
        'multi_dialog_completed': '✅ Опрос завершен',
        'feedback_completed': '✅ Отзыв отправлен!\nВаше мнение очень важно для нас!',
        'service_ticket_completed': '✅ Ваш тикет отправлен!\nМы учтем вашу проблему и займемся ее решением!',
        'data_sync_completed': '✅ Данные синхронизированы! \n\nС возвращением!\nПриступить к работе?',
        # ::prompts
        'multi_dialog_question_text_handler_prompt': '✏️ Введите ответ на вопрос:',
        'profile_name_text_handler_prompt': '✏️ Укажите свое имя\n\nПример: Иванов Иван Иванович',
        'profile_legal_entity_text_handler_prompt': '✏️ Укажите юридическое лицо\n\nПример: МТБ-Банк',
        'profile_object_text_handler_prompt': 'Выберите объект:',
        'feedback_text_handler_prompt': '✏️ Напишите ваше предложение:',
        'service_description_text_handler_prompt': '✏️ Опишите возникшую проблему:',
        'service_location_text_handler_prompt': '✏️ Укажите расположение возникшей проблемы:',
        'service_image_text_handler_prompt': '✏️ Отправьте изображение проблемы:',
        'user_agreement_input_handler_prompt': '❗ Вы даете согласие на обработку ваших персональных данных?',
        # ::headers
        'default_greeting': '👋 <b>Здравствуйте!</b>\nВас приветствует чат-бот управляющей компании Фард Сити {?}\n\n<b>📌 Этот бот обладает рядом функций:</b>\n<b>1. Обслуживание.</b> Через диалог с ботом вы можете подать заявку наобслуживание и ремонт. \n<b>2. Опрос.</b> В этом разделе вы можете пройти опрос, который позволит улучшить нам качество управления и обслуживания Норд Сити \n<b>3. Обратная связь.</b> Если у вас есть какие-то идеи или предложения о том, как улучшить Норд Сити, оставляйте их здесь.\n<b>4. Профиль.</b> С помощью меню вы можете изменить свою личную информацию \n\n<b>Выберите действие:</b>',
        'ma_greeting': '👋 <b>Здравствуйте!</b>\nВас приветствует чат-бот управляющей компании Фард Сити {?}\n\n<b>📌 Этот бот обладает рядом доступных для вас функций:</b>\n<b>1. Обслуживание.</b> Через диалог с ботом вы можете подать заявку наобслуживание и ремонт.\n<b>2. Профиль.</b> С помощью меню вы можете изменить свою личную информацию \n\n<b>Выберите действие:</b>',
        'profile_header': '👤 <b>Ваш профиль</b>\nЗдесь указана ваша личная информация необходимая для идентификации \n\n<b>Имя:</b>\n<i>{?}</i>\n\n<b>Юридическое лицо:</b>\n<i>{?}</i>\n\n<b>Объект:</b>\n<i>{?}</i>',
        'feedback_header': '🚩 <b>Обратная связь</b>\nВы можете отправить отзыв в администрацию Фард Сити, чтобы мы могли понять, как нам стать лучше\n\n<b>Текущий буфер:</b>\n<i>{?}</i>',
        'poll_header': '📊 <b>Опрос</b>\nПожалуйста, поделитесь с нами, что мы можем улучшить или изменить в Норд Сити, для того чтобы это место стало лучше для вас.\n\nНачать опрос?',
        'service_header': '🚩 <b>Поддержка</b>\nЗдесь вы можете оповестить администрацию обо всех возникших неудобствах.\n\n<b>Описание:</b>\n<i>{?}</i>\n\n<b>Местоположение:</b>\n<i>{?}</i>\n\n<b>Изображение:</b>\n<i>{?}</i>',
      },

    # English localization
    "EN": {
        # ::buttons
        'ratings_service': "Ratings",
      }
  }
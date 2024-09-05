from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_contact_keyboard():
    # Клавиатура для запроса контакта
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from datetime import date, time


class ConfirmationCallbackFactory(CallbackData, prefix="conf", sep='|'):
    type: str
    selected_date: date
    selected_time: time
    user_id: int


async def create_confirmation_buttons(selected_date: date, selected_time: time, user_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Подтвердить", callback_data=ConfirmationCallbackFactory(
        type="apply", selected_date=selected_date, selected_time=selected_time, user_id=user_id
    ).pack()))
    builder.add(InlineKeyboardButton(text="Отклонить", callback_data=ConfirmationCallbackFactory(
        type="decline", selected_date=selected_date, selected_time=selected_time, user_id=user_id
    ).pack()))

    return builder.as_markup()

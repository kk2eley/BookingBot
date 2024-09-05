from aiogram import Router
from aiogram.types import CallbackQuery

from core.keyboards.inline_buttons import ConfirmationCallbackFactory
from core.db.requests import update_booking_status

router = Router()


@router.callback_query(ConfirmationCallbackFactory.filter())
async def confirm_booking(callback: CallbackQuery, callback_data: ConfirmationCallbackFactory, session):
    button_type = callback_data.type
    date = callback_data.selected_date
    time = callback_data.selected_time
    user_id = callback_data.user_id

    text = callback.message.text.replace("Требуется подтверждение.", "")

    if button_type == "apply":
        await update_booking_status(session, date, time, "busy")
        msg_user = f"ВАШ ЗАКАЗ ПОДТВЕРЖДЁН{text}"
        msg_admin = f"ЗАКАЗ ПОДТВЕРЖДЁН{text}"
    else:
        await update_booking_status(session, date, time, "free")
        msg_user = f"ВАШ ЗАКАЗ ОТКЛОНЁН{text}"
        msg_admin = f"ЗАКАЗ ОТКЛОНЁН{text}"

    await callback.message.edit_text(msg_admin, reply_markup=None)
    await callback.message.bot.send_message(user_id, msg_user)

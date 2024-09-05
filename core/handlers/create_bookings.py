from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from aiogram_dialog import Dialog, DialogManager, StartMode, Window, setup_dialogs
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Calendar, Column, Multiselect, Button

import datetime as DT

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from core.db.models.booking import Booking
from core.db.requests import add_booking_times


class CreateBookingSQ(StatesGroup):
    choose_date = State()
    choose_times = State()
    finish = State()  # Дополнительное состояние для финального шага


async def on_date_selected(callback: CallbackQuery, widget,
                           dialog_manager: DialogManager, selected_date: DT.date):
    await callback.answer(str(selected_date))
    dialog_manager.dialog_data["selected_date"] = selected_date
    await dialog_manager.next()


async def get_times(dialog_manager: DialogManager, **kwargs):
    start = DT.datetime.combine(dialog_manager.dialog_data.get('selected_date'), DT.time(8, 00))
    step = 60
    count = 10
    times = []
    for i in range(count):
        time_obj = (start + DT.timedelta(minutes=(i * step))).time()
        time_str = time_obj.strftime("%H:%M")  # Формат для отображения

        times.append((time_obj, str(i), time_str))  # Сохраняем time_obj для обработки, а time_str для отображения

    dialog_manager.dialog_data["all_times"] = times
    return {"times": times}


async def on_times_confirmed(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    # Извлекаем сессию из dialog_data

    # Получаем данные о виджетах из текущего контекста
    widget_data = dialog_manager.current_context().widget_data

    # Извлекаем выбранные временные интервалы из widget_data
    selected_times = widget_data.get('working_time', [])
    print(selected_times)

    # Сохраняем выбранные интервалы времени в dialog_data для дальнейшего использования
    dialog_manager.dialog_data["selected_times"] = selected_times

    # Переходим в финальное состояние
    await dialog_manager.switch_to(CreateBookingSQ.finish)

    # Добавляем время бронирования, используя сессию
    async with AsyncSession(dialog_manager.dialog_data.get('engine')) as session:
        await add_booking_times(*await generate_bookings(dialog_manager.dialog_data.get("all_times"),
                                                         dialog_manager.dialog_data.get("selected_times"),
                                                         dialog_manager.dialog_data.get("selected_date")),
                                session=session)

    await dialog_manager.done()
    await callback.message.answer("Ваши рабочие часы сохранены")


# Асинхронный getter для финального окна
async def get_selected_times(dialog_manager: DialogManager, **kwargs):
    # Возвращаем данные из dialog_manager.dialog_data
    return dialog_manager.dialog_data


async def generate_bookings(all_times, selected_time_ids, date: DT.date):
    bookings = []
    for id in selected_time_ids:
        for item in all_times:
            print(id, item)
            if id == item[1]:  # item[0] это time_obj, item[1] это ID, item[2] это строка для отображения
                bookings.append(
                    Booking(status="free", time=item[0], date=date, datetime=DT.datetime.combine(date, item[0])))
    print(bookings)
    return bookings


create_booking_dialog = Dialog(
    Window(
        Format('Выберите дату'),
        Calendar(id='calendar', on_click=on_date_selected),
        state=CreateBookingSQ.choose_date
    ),
    Window(
        Format("Выберите время, в которое вы работаете:"),
        Column(
            Multiselect(
                checked_text=Format('[✔️] {item[2]}'),
                unchecked_text=Format('[ ] {item[2]}'),
                id="working_time",
                item_id_getter=lambda x: x[1],
                items="times"
            ),
        ),
        Button(
            text=Format("Подтвердить выбор"),
            id="confirm_button",
            on_click=on_times_confirmed
        ),
        state=CreateBookingSQ.choose_times,
        getter=get_times
    ),
)

router = Router()
router.include_router(create_booking_dialog)


@router.message(Command("add_working_time"))
async def begin_add_working_time_dialog(message: Message, session: AsyncSession, dialog_manager: DialogManager,
                                        engine: AsyncEngine):
    await dialog_manager.start(state=CreateBookingSQ.choose_date, mode=StartMode.RESET_STACK)
    dialog_manager.dialog_data['engine'] = engine

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from aiogram_dialog import DialogManager, Dialog, Window, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Format, Multi
from aiogram_dialog.widgets.kbd import Select, Button, Group, Multiselect

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.db.requests import get_dates, get_bookings_by_date, update_booking_status
from core.keyboards.contact_button import get_contact_keyboard
from core.keyboards.inline_buttons import create_confirmation_buttons
from core.other.get_data_text import line_dict
from core.settings import settings


class AppointmentSG(StatesGroup):
    choose_date = State()
    choose_time = State()
    chose_service = State()
    choose_additional_services = State()
    choose_ordering_option = State()
    request_contact = State()


async def get_dates_buttons(dialog_manager: DialogManager, **kwargs):
    items = []
    dates = dialog_manager.start_data.get("all_dates")
    for i in range(len(dates)):
        items.append((dates[i], str(i)))
    dialog_manager.dialog_data['dates'] = items
    return {'dates': items}


async def date_selection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, item_id: str):
    dates = dialog_manager.dialog_data.get("dates")
    for date, id in dates:
        if id == item_id:
            dialog_manager.dialog_data['selected_date'] = date
            break
    await dialog_manager.next()


async def get_times_buttons(dialog_manager: DialogManager, **kwargs):
    async with AsyncSession(dialog_manager.start_data.get("engine")) as session:
        bookings = await get_bookings_by_date(session, dialog_manager.dialog_data.get("selected_date"))
    items = []
    for i in range(len(bookings)):
        booking = bookings[i]
        items.append((str(booking.time.strftime("%H:%M")), str(i), booking.time))

    dialog_manager.dialog_data["times"] = items
    return {'times': items, 'selected_date': dialog_manager.dialog_data['selected_date']}


async def time_selection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, item_id: str,
                         **kwargs):
    selected_time = dialog_manager.dialog_data["times"][int(item_id)][2]
    selected_date = dialog_manager.dialog_data.get("selected_date")
    state = dialog_manager.start_data['state']
    await state.update_data({'selected_date': selected_date})
    await state.update_data({'selected_time': selected_time})
    dialog_manager.dialog_data["selected_time"] = selected_time
    async with AsyncSession(dialog_manager.start_data.get('engine')) as session:
        await update_booking_status(session, selected_date, selected_time, "process")
    await dialog_manager.next()


async def get_haircut_buttons(dialog_manager: DialogManager, **kwargs):
    haircut_prices = {
        "Ежик": 500,
        "Полубокс": 700,
        "Андеркат": 900,
        "Помпадур": 1200,
        "Фейд": 1300,
        "Квифф": 1400,
        "Классика с пробором": 1100,
        "Французский кроп": 1000,
        "Камбовер": 1500,
        "Мохавк": 1600,
        "Цезарь": 900,
        "Высокий и плотный": 800,
        "Иви Лиг": 1700,
        "Шэг": 1300,
        "Мужской пучок": 1800,
        "Тейпер": 1100,
        "Флеттоп": 900,
        "Зализанные назад": 2000
    }

    items = []
    for (haircut, price), i in zip(haircut_prices.items(), range(len(haircut_prices))):
        items.append((haircut, price, i))
    dialog_manager.dialog_data["haircuts"] = items
    return {"selected_date": dialog_manager.dialog_data.get('selected_date'),
            "selected_time": dialog_manager.dialog_data.get('selected_time').strftime("%H:%M"),
            "haircuts": items}


async def haircut_selection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['selected_haircut'] = dialog_manager.dialog_data['haircuts'][int(item_id)]
    await dialog_manager.next()


async def get_additional_service_buttons(dialog_manager: DialogManager, **kwargs):
    additional_services = {
        "Педикюр": 800,
        "Маникюр": 600,
        "Реснички": 500,
    }
    items = []
    for (service, price), i in zip(additional_services.items(), range(len(additional_services))):
        items.append((service, price, i))

    dialog_manager.dialog_data['additional_services'] = items

    haircut = dialog_manager.dialog_data["selected_haircut"][0]
    price = dialog_manager.dialog_data["selected_haircut"][1]
    date = dialog_manager.dialog_data.get("selected_date")
    time = dialog_manager.dialog_data.get("selected_time").strftime("%H:%M")
    chosen = dialog_manager.dialog_data.get("chosen", False)

    # Возвращаем уже выбранные услуги
    selected_services = dialog_manager.dialog_data.get("selected_services", [])
    selected_services_str = "\n".join([f"<b>{item[0]}</b> за <b>{item[1]}₽</b>" for item in selected_services])

    total = price
    for service in selected_services:
        total += service[1]

    dialog_manager.dialog_data['total'] = total

    ordering = dialog_manager.dialog_data.get('ordering', False)

    return {
        "additional_services": items,
        "haircut": haircut,
        "price": price,
        "date": date,
        "time": time,
        "selected_services_str": selected_services_str,  # Передаем выбранные услуги
        "chosen": chosen,
        "total": total,
        "ordering": ordering,
    }


async def select_additional_service(event, widget: Multiselect, dialog_manager: DialogManager, item_id: str):
    # Обработка выбора услуги
    selected_services_ids = map(int, widget.get_checked())
    selected_services = []
    for index in selected_services_ids:
        selected_services.append(dialog_manager.dialog_data["additional_services"][index])
    dialog_manager.dialog_data["selected_services"] = selected_services
    print(selected_services)
    dialog_manager.dialog_data['chosen'] = True if selected_services else False

    await dialog_manager.switch_to(AppointmentSG.choose_additional_services)


async def decline_additional_services(callback: CallbackQuery, button: Button,
                                      dialog_manager: DialogManager):
    dialog_manager.dialog_data['ordering'] = True


async def apply_additional_services(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['ordering'] = True


async def make_an_application(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()
    await callback.message.answer("Отправьте ваш контакт", reply_markup=await get_contact_keyboard())


async def payment_process(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    haircut = dialog_manager.dialog_data["selected_haircut"][0]
    price = dialog_manager.dialog_data["selected_haircut"][1]
    services = dialog_manager.dialog_data.get('selected_services', [])
    total = dialog_manager.dialog_data['total']

    prices = [LabeledPrice(label=haircut, amount=price * 100)]
    if services:
        for key, val, i in services:
            prices.append(LabeledPrice(label=key, amount=val * 100))

    await callback.bot.send_invoice(
        callback.message.chat.id,
        title='Оплата услуг в салоне "Крутышка"',
        description="После оплаты с вами свяжется наш самый быстрый менеджер в течении 5 минут",
        payload='telegram_order',
        provider_token="401643678:TEST:0d8e9ab8-d02a-450c-a071-92532a8e4fdc",
        currency='rub',
        prices=prices,
        max_tip_amount=10000,
        suggested_tip_amounts=[1000, 3000, 10000],
        need_name=True,
        need_phone_number=True
    )


async def clear_cart(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    engine = dialog_manager.start_data['engine']
    selected_date = dialog_manager.dialog_data['selected_date']
    selected_time = dialog_manager.dialog_data['selected_time']
    async with AsyncSession(engine) as session:
        await update_booking_status(session, selected_date, selected_time, "free")
    await dialog_manager.done()
    await callback.message.answer("Корзина очищена, чтобы начать заново пришлите /make_appointment")


async def process_contact(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    if message.contact:
        contact_number = message.contact.phone_number
        dialog_manager.dialog_data['phone'] = contact_number
        state = dialog_manager.start_data['state']
        await message.answer(f"Спасибо за заказ. Ваши данные переданы менеджеру. Ожидайте звонка.")
        text_user = await data_for_admin(dialog_manager.dialog_data, state)
        selected_date = dialog_manager.dialog_data['selected_date']
        selected_time = dialog_manager.dialog_data['selected_time']

        await message.bot.send_message(chat_id=settings.bot.admin_id, text=text_user,
                                       reply_markup=await create_confirmation_buttons(selected_date, selected_time,
                                                                                      message.from_user.id))
        await dialog_manager.done()


async def is_contact_sent(dialog_manager: DialogManager, **kwargs):
    first_answer = True
    return {'first_answer': first_answer}


appointment_dialog = Dialog(
    Window(
        Format("Выберите удобную дату"),
        Select(
            Format("{item[0]}"),
            id='date',
            item_id_getter=lambda x: x[1],
            items="dates",
            on_click=date_selection
        ),
        state=AppointmentSG.choose_date,
        getter=get_dates_buttons
    ),
    Window(
        Format("Выбранная дата: <b>{selected_date}</b>\n"
               "Выберите удобное время"),
        Group(
            Select(
                Format("{item[0]}"),
                id='time',
                item_id_getter=lambda x: x[1],
                items="times",
                on_click=time_selection
            ), width=5),
        state=AppointmentSG.choose_time,
        getter=get_times_buttons
    ),
    Window(
        Format("Выбранная дата: <b>{selected_date}</b>\n"
               "Выбранное время: <b>{selected_time}</b>\n"
               "Выберите стрижку"),
        Group(Select(
            Format("{item[0]}: {item[1]}₽"),
            id="haircut",
            item_id_getter=lambda x: x[2],
            items="haircuts",
            on_click=haircut_selection
        ), width=2),
        state=AppointmentSG.chose_service,
        getter=get_haircut_buttons
    ),
    Window(
        Format("Выбранная дата: <b>{date}</b>\n"
               "Выбранное время: <b>{time}</b>\n"
               "Ваша стрижка: <b>{haircut}</b> за <b>{price}₽</b>\n"
               "Я могу предложить вам одну из наших сопутствующих услуг:",
               when=lambda data, widget, manager: (not data['chosen']) and (not data['ordering'])),
        Multi(
            Format(
                "Выбранная дата: <b>{date}</b>\n"
                "Выбранное время: <b>{time}</b>\n"
                "Ваша стрижка: <b>{haircut}</b> за <b>{price}₽</b>\n"
            ),
            Format(
                "Сопутствующие услуги:\n"
                "{selected_services_str}\n",
                when=lambda data, widget, manager: data['selected_services_str'] != ''),
            Format(
                "Итого: <b>{total}₽</b>",
            ),
            when=lambda data, widget, manager: data['chosen'] or data['ordering'],
            sep='\n',
        ),
        # Определяем доступность кнопки по флагу
        Group(
            Group(Multiselect(
                checked_text=Format("✅{item[0]}: {item[1]}₽"),
                unchecked_text=Format("{item[0]}: {item[1]}₽"),
                id="additional_service",
                item_id_getter=lambda x: x[2],
                items="additional_services",
                on_state_changed=select_additional_service
            ), width=2
            ),
            Button(
                Format("Спасибо, не надо!"),
                id="decline",
                when=lambda data, widget, manager: not data['chosen'],
                on_click=decline_additional_services
            ),
            Button(
                Format("Пожалуй хватит"),
                id="done",
                when=lambda data, widget, manager: data['chosen'],
                on_click=apply_additional_services
            ),
            when=lambda data, widget, manager: not data['ordering']
        ),
        Group(
            Button(
                Format("Оформить заявку"),
                id="application",
                on_click=make_an_application,

            ),
            Button(
                Format("Перейти к оплате"),
                id="payment",
                on_click=payment_process,
            ),
            Button(
                Format("Очистить корзину"),
                id="clear_cart",
                on_click=clear_cart,
            ),
            when=lambda data, widget, manager: data['ordering'],
            width=2,
        ),
        state=AppointmentSG.choose_additional_services,
        getter=get_additional_service_buttons
    ),
    Window(
        Format("Спасибо за заказ!", when=lambda data, widget, manager: data.get('first_answer', True)),
        Format("Это не похоже на номер!", when=lambda data, widget, manager: not data.get('first_answer', True)),
        MessageInput(
            func=process_contact,
            content_types=ContentType.CONTACT,
        ),
        state=AppointmentSG.request_contact,
        getter=is_contact_sent
    ),
)

router = Router()
router.include_router(appointment_dialog)


@router.message(Command("make_appointment"))
async def make_appointment(message: Message, dialog_manager: DialogManager, session, engine: AsyncEngine,
                           state: FSMContext):
    # Получаем даты перед стартом диалога
    all_dates = await get_dates(session)

    # Запускаем диалог
    if all_dates:
        await dialog_manager.start(state=AppointmentSG.choose_date, mode=StartMode.RESET_STACK,
                                   data={"all_dates": all_dates, "engine": engine, "state": state})
    else:
        await message.answer("Нет свободных дат.")


async def data_for_admin(data, state) -> str:
    name = (await state.get_data()).get('name')
    phone = data['phone']

    date_needed = data['selected_date']
    time_needed = data['selected_time']
    haircut = data["selected_haircut"][0]
    price = data["selected_haircut"][1]
    services = data.get('selected_services', [])
    total = data['total']

    text_user = (f"<b>Требуется подтверждение.</b>\n\n"
                 f"Имя: <b>{name}</b>\nТелефон: <b>{phone}</b>\n"
                 f"Дата: <b>{date_needed}</b>\nВремя: <b>{time_needed}</b>\n"
                 f"Стрижка: <b>{haircut}</b> <b>{price}</b>\n")

    if services:
        text_user += "\nСопуствующие услуги:"

        for key, val, i in services:
            text_user += f"\n<b>{key} {val}</b>"

        text_user += f"\n\nСумма к оплате: <b>{total}</b>"

    return text_user


async def pre_checkout_query_answer(pre_checkout_query: PreCheckoutQuery, bot: Bot, state: FSMContext):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    line = line_dict(pre_checkout_query.dict())
    await bot.send_message(chat_id=settings.bot.admin_id, text=line)


async def buy_complete(message: Message, session: AsyncSession, state: FSMContext):
    msg = (
        f'Спасибо за оплату {message.successful_payment.total_amount // 100} {message.successful_payment.currency}. \r\n'
        f'Наш менеджер получил заявку и уже набирает ваш номер телефона.')
    await message.answer(msg)

    data = await state.get_data()
    selected_date = data['selected_date']
    selected_time = data['selected_time']

    await update_booking_status(session, selected_date, selected_time, "paid")
    await state.set_data({'name': data.get('name', message.from_user.first_name)})

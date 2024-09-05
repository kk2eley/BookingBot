from datetime import datetime, date, time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, distinct, asc, func, update

from core.db import User, Booking


async def add_booking_times(*bookings, session: AsyncSession):
    try:
        # Добавляем все записи
        session.add_all(bookings)

        # Подтверждаем транзакцию
        await session.commit()
        print("Бронирования успешно добавлены в базу данных.")

    except SQLAlchemyError as e:
        # В случае ошибки откатываем транзакцию
        await session.rollback()
        print(f"Ошибка при добавлении бронирований: {e}")


async def insert_user(
        session: AsyncSession,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
):
    """
    Добавление или обновление пользователя
    в таблице users
    :param session: сессия СУБД
    :param telegram_id: айди пользователя
    :param first_name: имя пользователя
    :param last_name: фамилия пользователя
    """
    stmt = insert(User).values(
        {
            "telegram_id": telegram_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username
        }
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['telegram_id'],
        set_=dict(
            first_name=first_name,
            last_name=last_name,
        ),
    )
    await session.execute(stmt)
    await session.commit()


async def get_dates(session: AsyncSession):
    # Получаем текущую дату
    today = datetime.today().date()

    # SQL-запрос для получения 10 ближайших уникальных дат, начиная с сегодняшней, где статус "free"
    stmt = (
        select(Booking.date)
        .filter(Booking.date >= today)  # Фильтрация по дате начиная с сегодняшней
        .filter(Booking.status == "free")  # Фильтрация по статусу "free"
        .group_by(Booking.date)  # Группировка по датам
        .order_by(asc(Booking.date))  # Сортировка по дате по возрастанию
        .limit(10)  # Ограничение на 10 ближайших дат
    )

    # Выполняем запрос
    result = await session.execute(stmt)

    # Извлекаем уникальные даты
    dates = result.scalars().all()

    return dates


async def get_bookings_by_date(session: AsyncSession, booking_date: date):
    # Создаем SQL-запрос для получения всех полей из таблицы Booking для заданной даты и сортировки по времени, где статус "free"
    stmt = (
        select(Booking)  # Выбираем все поля из таблицы Booking
        .filter(Booking.date == booking_date)  # Фильтрация по заданной дате
        .filter(Booking.status == "free")  # Фильтрация по статусу "free"
        .order_by(Booking.time.asc())  # Сортировка по времени по возрастанию
    )

    # Выполняем запрос
    result = await session.execute(stmt)

    # Извлекаем все строки, соответствующие дате
    bookings = result.scalars().all()

    return bookings


async def update_booking_status(session: AsyncSession, booking_date: date, booking_time: time, status):
    # Создаем SQL-запрос для обновления статуса строки в таблице Booking
    stmt = (
        update(Booking)  # Обновляем таблицу Booking
        .where(Booking.date == booking_date)  # Фильтруем по дате
        .where(Booking.time == booking_time)  # Фильтруем по времени
        .values(status=status)  # Устанавливаем новое значение для поля status
    )

    # Выполняем запрос
    await session.execute(stmt)
    await session.commit()  # Подтверждаем изменения в базе данных

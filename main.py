import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType


from aiogram_dialog import setup_dialogs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy import text

from core.handlers import get_routers
from core.middlewares.session import DbSessionMiddleware
from core.middlewares.track_all_users import TrackAllUsersMiddleware
from core.settings import settings
from core.db import Base
from core.handlers.make_appointment import pre_checkout_query_answer, buy_complete


async def start_bot(bot: Bot):
    await bot.send_message(chat_id=settings.bot.admin_id, text="Started")


async def stop_bot(bot: Bot):
    await bot.send_message(chat_id=settings.bot.admin_id, text="Stopped")


async def get_engine(dsn, echo) -> AsyncEngine:
    engine = create_async_engine(
        url=dsn,
        echo=echo
    )

    # Открытие нового соединение с базой
    async with engine.begin() as conn:
        # Выполнение обычного текстового запроса
        await conn.execute(text("SELECT 1"))

    return engine


async def create_tables(engine: AsyncEngine):
    # Создание таблиц
    async with engine.begin() as connection:
        # Если ловите ошибку "таблица уже существует",
        # раскомментируйте следующую строку:
        # await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def run_bot():
    logging.basicConfig(
        level=logging.INFO
    )

    bot = Bot(token=settings.bot.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    engine = await get_engine(settings.db.dsn, settings.db.echo)
    dp['engine'] = engine
    Sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    await create_tables(engine)

    dp.update.outer_middleware(DbSessionMiddleware(Sessionmaker))
    dp.message.outer_middleware(TrackAllUsersMiddleware())

    dp.message.register(buy_complete, F.content_type == ContentType.SUCCESSFUL_PAYMENT)
    dp.pre_checkout_query.register(pre_checkout_query_answer)
    dp.include_routers(*get_routers())

    setup_dialogs(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except(KeyboardInterrupt, SystemExit):
        print("Error")

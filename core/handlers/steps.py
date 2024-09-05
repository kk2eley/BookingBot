from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from core.keyboards.text_button import get_button_name
from core.other.states import AcquaintanceSG

router = Router()


@router.message(StateFilter(AcquaintanceSG.state_name))
async def get_data(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(f"Приятно познакомиться {message.text}, чтобы записаться на стрижку пришли /make_appointment")
    await state.update_data(name=message.text)
    await state.set_state(AcquaintanceSG.state_date)


@router.message(CommandStart())
async def get_name(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer("Привет я помощник салона красоты \"Крутышка\". Как я могу к тебе обращаться?",
                         reply_markup=await get_button_name(message.from_user.first_name))
    await state.set_state(AcquaintanceSG.state_name)

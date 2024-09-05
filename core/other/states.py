from aiogram.fsm.state import StatesGroup, State

class AcquaintanceSG(StatesGroup):
    state_name = State()
    state_date = State()
    state_time = State()
    state_service = State()
    state_add_service = State()
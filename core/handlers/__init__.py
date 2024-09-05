from aiogram import Router

from . import steps, create_bookings, make_appointment, booking_confirmation


def get_routers() -> list[Router]:
    return [
        booking_confirmation.router,
        steps.router,
        create_bookings.router,
        make_appointment.router,

    ]

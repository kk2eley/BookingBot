from datetime import datetime, date, time

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, TIMESTAMP, func, Date, Text, String, ForeignKey, Time

from core.db import Base


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'), nullable=True)

    user = relationship("User", back_populates="bookings")

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase


class Company(TimestampedBase):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200), index=True)
    users = relationship("User", back_populates="company")

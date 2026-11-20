import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase


class Role(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    SAFETY_MANAGER = "SAFETY_MANAGER"
    VIEWER = "VIEWER"


class User(TimestampedBase):
    __tablename__ = "users"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=20), default=Role.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship("Company", back_populates="users")

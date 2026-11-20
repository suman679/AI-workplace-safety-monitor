import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase


class Worker(TimestampedBase):
    __tablename__ = "workers"
    __table_args__ = (UniqueConstraint("company_id", "employee_code", name="uq_worker_company_code"),)

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="SET NULL"), index=True, nullable=True)
    employee_code: Mapped[str] = mapped_column(String(40))
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    site = relationship("Site", back_populates="workers")

    @property
    def site_name(self) -> str | None:
        return self.site.name if self.site else None

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase
from app.models.enums import PpeItem, Severity


class PpeRule(TimestampedBase):
    __tablename__ = "ppe_rules"
    __table_args__ = (UniqueConstraint("site_id", "ppe_item", name="uq_ppe_rule_site_item"),)

    site_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    ppe_item: Mapped[PpeItem] = mapped_column(Enum(PpeItem, native_enum=False, length=20))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, native_enum=False, length=20), default=Severity.MEDIUM)

    site = relationship("Site", back_populates="rules")

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase
from app.models.enums import CameraStatus, SourceType


class Camera(TimestampedBase):
    __tablename__ = "cameras"
    __table_args__ = (UniqueConstraint("company_id", "camera_code", name="uq_camera_company_code"),)

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    camera_code: Mapped[str] = mapped_column(String(40))
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[CameraStatus] = mapped_column(Enum(CameraStatus, native_enum=False, length=20), default=CameraStatus.OFFLINE)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=False, length=20), default=SourceType.WEBCAM)
    stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    site = relationship("Site", back_populates="cameras")

    @property
    def site_name(self) -> str:
        return self.site.name

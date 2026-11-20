import uuid

from sqlalchemy import JSON, Enum, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import TimestampedBase
from app.models.enums import JobStatus


class DetectionJob(TimestampedBase):
    """A background video analysis."""

    __tablename__ = "detection_jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_name: Mapped[str] = mapped_column(String(255))
    input_path: Mapped[str] = mapped_column(String(500))
    output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, native_enum=False, length=20), default=JobStatus.QUEUED)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String(300), nullable=True)

    @property
    def has_output(self) -> bool:
        return self.output_path is not None

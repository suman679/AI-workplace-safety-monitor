import uuid

from sqlalchemy import Enum, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedBase
from app.models.enums import PpeItem, SiteType


class Site(TimestampedBase):
    __tablename__ = "sites"

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    site_type: Mapped[SiteType] = mapped_column(Enum(SiteType, native_enum=False, length=20), default=SiteType.OTHER)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    safety_threshold: Mapped[float] = mapped_column(Float, default=80.0)

    rules = relationship("PpeRule", back_populates="site", cascade="all, delete-orphan")
    cameras = relationship("Camera", back_populates="site", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="site")

    @property
    def required_ppe(self) -> list[PpeItem]:
        order = list(PpeItem)
        return sorted((r.ppe_item for r in self.rules if r.is_required), key=order.index)

    @property
    def camera_count(self) -> int:
        return len(self.cameras)

    @property
    def worker_count(self) -> int:
        return len(self.workers)

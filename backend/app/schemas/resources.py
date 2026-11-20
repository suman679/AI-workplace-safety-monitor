import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CameraStatus, PpeItem, Severity, SiteType, SourceType


class Strip(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- sites ----
class SiteCreate(Strip):
    name: str = Field(min_length=2, max_length=150)
    site_type: SiteType = SiteType.OTHER
    address: str | None = Field(default=None, max_length=300)
    safety_threshold: float = Field(default=80.0, ge=0, le=100)
    required_ppe: list[PpeItem] | None = None  # omitted -> defaults for the site type


class SiteUpdate(Strip):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    site_type: SiteType | None = None
    address: str | None = Field(default=None, max_length=300)
    safety_threshold: float | None = Field(default=None, ge=0, le=100)
    required_ppe: list[PpeItem] | None = None


class SiteOut(Orm):
    id: uuid.UUID
    name: str
    site_type: SiteType
    address: str | None
    safety_threshold: float
    required_ppe: list[PpeItem]
    camera_count: int
    worker_count: int
    created_at: datetime


# ---- ppe rules ----
class PpeRuleUpdate(BaseModel):
    is_required: bool | None = None
    severity: Severity | None = None


class PpeRuleOut(Orm):
    id: uuid.UUID
    site_id: uuid.UUID
    ppe_item: PpeItem
    is_required: bool
    severity: Severity


# ---- cameras ----
class CameraCreate(Strip):
    name: str = Field(min_length=2, max_length=150)
    camera_code: str = Field(min_length=1, max_length=40)
    site_id: uuid.UUID
    location: str | None = Field(default=None, max_length=200)
    source_type: SourceType = SourceType.WEBCAM
    stream_url: str | None = Field(default=None, max_length=500)
    status: CameraStatus = CameraStatus.OFFLINE

    @model_validator(mode="after")
    def rtsp_needs_url(self):
        if self.source_type == SourceType.RTSP and not (self.stream_url or "").lower().startswith(("rtsp://", "rtsps://")):
            raise ValueError("RTSP cameras need a stream URL starting with rtsp://")
        return self


class CameraUpdate(Strip):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    camera_code: str | None = Field(default=None, min_length=1, max_length=40)
    site_id: uuid.UUID | None = None
    location: str | None = Field(default=None, max_length=200)
    source_type: SourceType | None = None
    stream_url: str | None = Field(default=None, max_length=500)
    status: CameraStatus | None = None


class CameraOut(Orm):
    id: uuid.UUID
    name: str
    camera_code: str
    site_id: uuid.UUID
    site_name: str
    location: str | None
    status: CameraStatus
    source_type: SourceType
    stream_url: str | None
    last_active_at: datetime | None


# ---- workers ----
class WorkerCreate(Strip):
    employee_code: str = Field(min_length=1, max_length=40)
    full_name: str = Field(min_length=2, max_length=120)
    site_id: uuid.UUID | None = None
    department: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class WorkerUpdate(Strip):
    employee_code: str | None = Field(default=None, min_length=1, max_length=40)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    site_id: uuid.UUID | None = None
    department: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class WorkerOut(Orm):
    id: uuid.UUID
    employee_code: str
    full_name: str
    site_id: uuid.UUID | None
    site_name: str | None
    department: str | None
    is_active: bool


# ---- dashboard ----
class DashboardStats(BaseModel):
    total_sites: int
    total_cameras: int
    online_cameras: int
    total_workers: int
    active_workers: int
    cameras_by_status: dict[str, int]


# ---- detection jobs ----
import uuid as _uuid  # noqa: E402

from app.models.enums import JobStatus  # noqa: E402


class JobOut(Orm):
    id: _uuid.UUID
    original_name: str
    site_id: _uuid.UUID | None
    status: JobStatus
    progress: float
    summary: dict | None
    error: str | None
    has_output: bool
    created_at: datetime

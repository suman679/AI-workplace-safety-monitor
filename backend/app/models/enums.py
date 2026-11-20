import enum


class PpeItem(str, enum.Enum):
    HELMET = "HELMET"
    VEST = "VEST"
    GLOVES = "GLOVES"
    SAFETY_SHOES = "SAFETY_SHOES"
    MASK = "MASK"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SiteType(str, enum.Enum):
    CONSTRUCTION = "CONSTRUCTION"
    FACTORY = "FACTORY"
    WAREHOUSE = "WAREHOUSE"
    OTHER = "OTHER"


class CameraStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    WARNING = "WARNING"


class SourceType(str, enum.Enum):
    WEBCAM = "WEBCAM"
    VIDEO = "VIDEO"
    RTSP = "RTSP"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

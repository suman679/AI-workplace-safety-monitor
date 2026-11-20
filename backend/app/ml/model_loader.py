"""Loads the YOLO model once and reuses it. ultralytics/torch are imported lazily so the API runs without them."""
import importlib.util
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import get_settings
from app.ml.class_map import classify_label, ppe_support
from app.models.enums import PpeItem

log = logging.getLogger("safevision.ml")
DEMO_MODEL = "yolov8n.pt"  # COCO weights: finds people only, no PPE


class ModelUnavailable(Exception):
    """Raised when AI libraries or weights are missing; the API turns it into a 503."""


@dataclass
class ModelHandle:
    yolo: object
    names: dict
    class_kinds: dict
    support: dict[PpeItem, str]
    source: str  # "custom" or "demo"
    path: str
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def ppe_capable(self) -> bool:
        return bool(self.support)


_handle: ModelHandle | None = None
_load_lock = threading.Lock()


def ml_installed() -> bool:
    return importlib.util.find_spec("ultralytics") is not None


def model_status() -> dict:
    """Cheap status for the UI. Never triggers a model load or download."""
    s = get_settings()
    h = _handle
    return {
        "ml_installed": ml_installed(),
        "model_file_found": Path(s.MODEL_PATH).is_file(),
        "loaded": h is not None,
        "source": h.source if h else None,
        "ppe_capable": h.ppe_capable if h else None,
        "supported_ppe": sorted(i.value for i in h.support) if h else None,
        "confidence_threshold": s.CONFIDENCE_THRESHOLD,
    }


def get_model() -> ModelHandle:
    global _handle
    if _handle is not None:
        return _handle
    with _load_lock:
        if _handle is not None:
            return _handle
        if not ml_installed():
            raise ModelUnavailable("AI libraries are not installed. Run: pip install -r requirements-ml.txt")
        from ultralytics import YOLO

        custom = Path(get_settings().MODEL_PATH)
        source, path = ("custom", str(custom)) if custom.is_file() else ("demo", DEMO_MODEL)
        try:
            yolo = YOLO(path)
        except Exception as exc:  # corrupt weights, offline download failure, ...
            log.exception("Failed to load model %s", path)
            raise ModelUnavailable("Could not load the AI model (see the backend log for details).") from exc
        names = dict(yolo.names)
        kinds = {i: k for i, n in names.items() if (k := classify_label(n))}
        if not any(k == "person" for k, _ in kinds.values()):
            raise ModelUnavailable("The model must include a 'person' class.")
        _handle = ModelHandle(yolo, names, kinds, ppe_support(kinds), source, path)
        log.info("Loaded %s model %s (PPE items: %s)", source, path, sorted(i.value for i in _handle.support))
        return _handle

from dataclasses import dataclass

import numpy as np

from app.core.config import get_settings
from app.ml.model_loader import get_model
from app.models.enums import PpeItem


@dataclass
class Detection:
    kind: str  # "person" | "has" | "missing"
    item: PpeItem | None
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels
    conf: float
    label: str


def detect(frame: np.ndarray) -> list[Detection]:
    """Runs YOLO on one BGR frame and keeps only classes SafeVision understands."""
    model = get_model()
    s = get_settings()
    with model.lock:  # one inference at a time per loaded model
        result = model.yolo.predict(frame, conf=s.CONFIDENCE_THRESHOLD, imgsz=s.DETECTION_IMAGE_SIZE, verbose=False)[0]
    out: list[Detection] = []
    if result.boxes is None:
        return out
    xyxy = result.boxes.xyxy.cpu().numpy()
    confs = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy().astype(int)
    for box, conf, cls in zip(xyxy, confs, classes):
        kind = model.class_kinds.get(int(cls))
        if kind:
            out.append(Detection(kind[0], kind[1], tuple(float(v) for v in box), float(conf), model.names[int(cls)]))
    return out

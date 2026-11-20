"""Drawing and JSON serialisation of detection results."""
import cv2
import numpy as np

from app.ml.detector import Detection
from app.ml.rule_engine import ITEM_LABEL, PersonResult
from app.models.enums import PpeItem

COLORS = {"SAFE": (80, 200, 60), "WARNING": (0, 190, 245), "VIOLATION": (60, 60, 235)}  # BGR
PPE_COLOR = (200, 140, 40)
KEYS = {PpeItem.HELMET: "helmet", PpeItem.VEST: "vest", PpeItem.GLOVES: "gloves", PpeItem.SAFETY_SHOES: "safety_shoes", PpeItem.MASK: "mask"}


def person_label(r: PersonResult) -> str:
    text = f"ID {r.person_id} {int(r.confidence * 100)}%"
    if r.violations:
        text += " | " + ", ".join(f"No {ITEM_LABEL[i]}" for i in r.violations)
    elif r.state == "SAFE":
        text += " | OK"
    else:
        text += " | PPE not checked" if r.unchecked else ""
    return text


def annotate(frame: np.ndarray, persons: list[PersonResult], ppe: list[Detection]) -> np.ndarray:
    out = frame.copy()
    for d in ppe:
        x1, y1, x2, y2 = (int(v) for v in d.box)
        cv2.rectangle(out, (x1, y1), (x2, y2), PPE_COLOR, 1)
    thick = max(2, round(max(out.shape[:2]) / 400))
    scale = max(0.45, max(out.shape[:2]) / 1600)
    for r in persons:
        x1, y1, x2, y2 = (int(v) for v in r.box)
        color = COLORS[r.state]
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thick)
        text = person_label(r)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        top = max(0, y1 - th - 8)
        cv2.rectangle(out, (x1, top), (x1 + tw + 8, top + th + 8), color, -1)
        cv2.putText(out, text, (x1 + 4, top + th + 2), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def _norm_box(box, w, h):
    return [round(box[0] / w, 4), round(box[1] / h, 4), round(box[2] / w, 4), round(box[3] / h, 4)]


def person_to_dict(r: PersonResult, w: int, h: int) -> dict:
    d = {"person_id": r.person_id}
    d.update({KEYS[i]: r.items[i] for i in PpeItem})
    d.update(
        compliance_score=r.compliance_score,
        violations=[f"Missing {ITEM_LABEL[i]}" for i in r.violations],
        not_checked=[ITEM_LABEL[i] for i in r.unchecked],
        confidence=round(r.confidence, 2),
        state=r.state,
        severity=r.severity.value if r.severity else None,
        box=_norm_box(r.box, w, h),
    )
    return d


def ppe_to_dict(d: Detection, w: int, h: int) -> dict:
    return {"item": d.item.value, "kind": d.kind, "confidence": round(d.conf, 2), "box": _norm_box(d.box, w, h)}

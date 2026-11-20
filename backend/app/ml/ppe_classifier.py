"""Decides which detected PPE belongs to which person, using box geometry."""
from dataclasses import dataclass, field

from app.ml.detector import Detection
from app.models.enums import PpeItem

# Vertical band of a person's box (fraction of height from the top) where each PPE item is expected.
ZONES: dict[PpeItem, tuple[float, float]] = {
    PpeItem.HELMET: (-0.15, 0.35),
    PpeItem.MASK: (-0.05, 0.50),
    PpeItem.VEST: (0.15, 0.75),
    PpeItem.GLOVES: (0.20, 1.00),
    PpeItem.SAFETY_SHOES: (0.65, 1.15),
}
H_MARGIN = 0.15  # tolerate PPE slightly outside the person box horizontally


@dataclass
class PersonPpe:
    person: Detection
    has: dict[PpeItem, float] = field(default_factory=dict)      # item -> best confidence
    missing: dict[PpeItem, float] = field(default_factory=dict)


def _overlap_fraction(inner: tuple, outer: tuple) -> float:
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    area = max(0.0, inner[2] - inner[0]) * max(0.0, inner[3] - inner[1])
    if area <= 0:
        return 0.0
    return max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1) / area


def _in_zone(person: Detection, ppe: Detection) -> bool:
    x1, y1, x2, y2 = person.box
    w, h = x2 - x1, y2 - y1
    cx, cy = (ppe.box[0] + ppe.box[2]) / 2, (ppe.box[1] + ppe.box[3]) / 2
    lo, hi = ZONES[ppe.item]
    return x1 - H_MARGIN * w <= cx <= x2 + H_MARGIN * w and y1 + lo * h <= cy <= y1 + hi * h


def associate(detections: list[Detection]) -> list[PersonPpe]:
    persons = [PersonPpe(d) for d in detections if d.kind == "person"]
    for det in detections:
        if det.kind == "person" or det.item is None:
            continue
        candidates = [p for p in persons if _in_zone(p.person, det)]
        if not candidates:
            continue
        dcx = (det.box[0] + det.box[2]) / 2

        def score(p: PersonPpe):
            pw = max(1.0, p.person.box[2] - p.person.box[0])
            pcx = (p.person.box[0] + p.person.box[2]) / 2
            return (_overlap_fraction(det.box, p.person.box), -abs(dcx - pcx) / pw)

        best = max(candidates, key=score)
        bucket = best.has if det.kind == "has" else best.missing
        bucket[det.item] = max(det.conf, bucket.get(det.item, 0.0))
    return persons

import uuid

from sqlalchemy.orm import Session

from app.api.deps import get_owned
from app.core.config import get_settings
from app.ml import postprocessing, preprocessing
from app.ml.detector import detect
from app.ml.model_loader import get_model
from app.ml.ppe_classifier import associate
from app.ml.rule_engine import DEFAULT_RULES, PersonResult, RuleSpec, evaluate, summarize
from app.ml.tracker import Tracker
from app.models import Site


def load_rules(db: Session, company_id: uuid.UUID, site_id: uuid.UUID | None) -> list[RuleSpec]:
    if site_id is None:
        return list(DEFAULT_RULES)
    site = get_owned(db, Site, site_id, company_id)
    return [RuleSpec(r.ppe_item, r.is_required, r.severity) for r in site.rules]


def analyze_frame(frame, rules: list[RuleSpec], tracker: Tracker | None = None):
    """Full pipeline for one BGR frame -> (person results, ppe detections)."""
    detections = detect(frame)
    support = get_model().support
    associated = associate(detections)
    ids = tracker.update([p.person.box for p in associated]) if tracker else list(range(1, len(associated) + 1))
    persons = [evaluate(pp, pid, rules, support) for pp, pid in zip(associated, ids)]
    ppe = [d for d in detections if d.kind != "person"]
    return persons, ppe


def result_payload(frame, persons: list[PersonResult], ppe) -> dict:
    h, w = frame.shape[:2]
    return {
        "width": w,
        "height": h,
        "ppe_capable": get_model().ppe_capable,
        "persons": [postprocessing.person_to_dict(p, w, h) for p in persons],
        "ppe_detections": [postprocessing.ppe_to_dict(d, w, h) for d in ppe],
        "summary": summarize(persons),
    }


def analyze_bytes(data: bytes, rules: list[RuleSpec], tracker: Tracker | None = None):
    """Decode, resize and analyse an encoded image. Returns (resized frame, persons, ppe)."""
    frame = preprocessing.limit_size(preprocessing.decode_image(data), get_settings().MAX_FRAME_SIDE)
    persons, ppe = analyze_frame(frame, rules, tracker)
    return frame, persons, ppe

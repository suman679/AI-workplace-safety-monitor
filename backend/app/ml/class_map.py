"""Maps a model's class names onto SafeVision concepts, so any reasonably-named PPE dataset works.

Supports positive classes ("helmet", "Hardhat") and negative classes ("no-helmet", "NO-Hardhat").
"""
import re

from app.models.enums import PpeItem

POSITIVE_NAMES: dict[PpeItem, set[str]] = {
    PpeItem.HELMET: {"helmet", "hardhat", "hard hat", "safety helmet", "safety hat"},
    PpeItem.VEST: {"vest", "safety vest", "hi vis vest", "reflective vest", "high vis vest"},
    PpeItem.GLOVES: {"gloves", "glove", "safety gloves"},
    PpeItem.SAFETY_SHOES: {"safety shoes", "safety shoe", "safety boots", "safety boot", "boots", "boot", "shoes"},
    PpeItem.MASK: {"mask", "face mask", "facemask"},
}
PERSON_NAMES = {"person", "worker", "people"}
NEGATIVE_PREFIXES = ("no ", "without ", "missing ")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]+", " ", name.lower()).strip()


def _lookup(name: str) -> PpeItem | None:
    for item, names in POSITIVE_NAMES.items():
        if name in names:
            return item
    return None


def classify_label(name: str) -> tuple[str, PpeItem | None] | None:
    """Returns ("person", None), ("has", item), ("missing", item) or None for irrelevant classes."""
    n = _norm(name)
    if n in PERSON_NAMES:
        return "person", None
    for prefix in NEGATIVE_PREFIXES:
        if n.startswith(prefix):
            item = _lookup(n[len(prefix):])
            if item:
                return "missing", item
    item = _lookup(n)
    return ("has", item) if item else None


def ppe_support(kinds: dict[int, tuple[str, PpeItem | None]]) -> dict[PpeItem, str]:
    """Which PPE items the model can judge, and how: positive, negative or both class types."""
    seen: dict[PpeItem, set[str]] = {}
    for kind, item in kinds.values():
        if item is not None:
            seen.setdefault(item, set()).add(kind)
    return {
        item: "both" if len(k) == 2 else ("positive" if "has" in k else "negative")
        for item, k in seen.items()
    }

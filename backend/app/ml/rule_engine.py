"""Turns associated PPE into per-person compliance using the site's configurable rules."""
from dataclasses import dataclass, field

from app.ml.ppe_classifier import PersonPpe
from app.models.enums import PpeItem, Severity

SEVERITY_ORDER = list(Severity)
ITEM_LABEL = {
    PpeItem.HELMET: "Helmet", PpeItem.VEST: "Vest", PpeItem.GLOVES: "Gloves",
    PpeItem.SAFETY_SHOES: "Safety Shoes", PpeItem.MASK: "Mask",
}


@dataclass
class RuleSpec:
    item: PpeItem
    required: bool
    severity: Severity = Severity.MEDIUM


DEFAULT_RULES = [
    RuleSpec(PpeItem.HELMET, True, Severity.HIGH),
    RuleSpec(PpeItem.VEST, True, Severity.HIGH),
]


@dataclass
class PersonResult:
    person_id: int
    box: tuple[float, float, float, float]  # pixels
    confidence: float
    items: dict[PpeItem, bool | None]       # True worn, False missing, None model cannot tell
    violations: list[PpeItem] = field(default_factory=list)
    unchecked: list[PpeItem] = field(default_factory=list)
    compliance_score: float | None = None
    state: str = "WARNING"                  # SAFE | WARNING | VIOLATION
    severity: Severity | None = None


def item_status(pp: PersonPpe, item: PpeItem, support: dict[PpeItem, str]) -> bool | None:
    mode = support.get(item)
    if mode is None:
        return None                      # model has no class for this item: cannot judge
    if item in pp.has and item in pp.missing:
        return pp.has[item] >= pp.missing[item]
    if item in pp.has:
        return True
    if item in pp.missing:
        return False
    # Nothing found for this item:
    #  positive-only model -> not seen means missing
    #  negative-only model -> no "no-x" box means no violation was seen
    #  model with both     -> it would have said so either way, so we cannot tell (never a guessed violation)
    if mode == "positive":
        return False
    if mode == "negative":
        return True
    return None


def evaluate(pp: PersonPpe, person_id: int, rules: list[RuleSpec], support: dict[PpeItem, str]) -> PersonResult:
    items = {item: item_status(pp, item, support) for item in PpeItem}
    result = PersonResult(person_id, pp.person.box, pp.person.conf, items)
    required = [r for r in rules if r.required]
    judged = 0
    worn = 0
    for rule in required:
        status = items[rule.item]
        if status is None:
            result.unchecked.append(rule.item)
        else:
            judged += 1
            if status:
                worn += 1
            else:
                result.violations.append(rule.item)
    if result.violations:
        result.state = "VIOLATION"
        sev = [r.severity for r in required if r.item in result.violations]
        result.severity = max(sev, key=SEVERITY_ORDER.index)
    elif judged and not result.unchecked:
        result.state = "SAFE"
    elif judged:
        result.state = "WARNING"
    else:
        result.state = "WARNING"
    result.compliance_score = round(100 * worn / judged, 1) if judged else None
    return result


def summarize(results: list[PersonResult]) -> dict:
    scored = [r.compliance_score for r in results if r.compliance_score is not None]
    return {
        "workers": len(results),
        "compliant": sum(r.state == "SAFE" for r in results),
        "violations": sum(r.state == "VIOLATION" for r in results),
        "warnings": sum(r.state == "WARNING" for r in results),
        "safety_score": round(sum(scored) / len(scored), 1) if scored else None,
    }

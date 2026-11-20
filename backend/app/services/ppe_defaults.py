"""Default PPE rules applied when a site is created. Admins can change them per site afterwards."""
from app.models.enums import PpeItem, Severity, SiteType

DEFAULT_REQUIRED: dict[SiteType, set[PpeItem]] = {
    SiteType.CONSTRUCTION: {PpeItem.HELMET, PpeItem.VEST, PpeItem.SAFETY_SHOES},
    SiteType.FACTORY: {PpeItem.HELMET, PpeItem.SAFETY_SHOES, PpeItem.GLOVES},
    SiteType.WAREHOUSE: {PpeItem.VEST, PpeItem.SAFETY_SHOES},
    SiteType.OTHER: {PpeItem.HELMET},
}

DEFAULT_SEVERITY: dict[PpeItem, Severity] = {
    PpeItem.HELMET: Severity.HIGH,
    PpeItem.VEST: Severity.HIGH,
    PpeItem.GLOVES: Severity.MEDIUM,
    PpeItem.SAFETY_SHOES: Severity.MEDIUM,
    PpeItem.MASK: Severity.LOW,
}

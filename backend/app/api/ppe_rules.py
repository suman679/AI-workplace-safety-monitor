import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import WRITERS, company_id_of, get_current_user, get_owned, require_roles
from app.database.session import get_db
from app.models import PpeRule, Site, User
from app.schemas.resources import PpeRuleOut, PpeRuleUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/api/ppe-rules", tags=["ppe-rules"])


@router.get("", response_model=list[PpeRuleOut])
def list_rules(site_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    site = get_owned(db, Site, site_id, company_id_of(user))
    return db.scalars(select(PpeRule).where(PpeRule.site_id == site.id)).all()


@router.put("/{rule_id}", response_model=PpeRuleOut)
def update_rule(rule_id: uuid.UUID, body: PpeRuleUpdate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    rule = db.get(PpeRule, rule_id)
    if rule is None or rule.site.company_id != company_id_of(user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PpeRule not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(rule, key, value)
    db.commit()
    write_audit(db, "PPE_RULE_UPDATED", request, user.id, f"{rule.site.name}: {rule.ppe_item.value}")
    return rule

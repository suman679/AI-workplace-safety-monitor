import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import ADMINS, WRITERS, company_id_of, get_current_user, get_owned, require_roles
from app.database.session import get_db
from app.models import PpeItem, PpeRule, Site, User
from app.schemas.resources import SiteCreate, SiteOut, SiteUpdate
from app.services.audit import write_audit
from app.services.ppe_defaults import DEFAULT_REQUIRED, DEFAULT_SEVERITY

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("", response_model=list[SiteOut])
def list_sites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(Site)
        .where(Site.company_id == company_id_of(user))
        .options(selectinload(Site.rules), selectinload(Site.cameras), selectinload(Site.workers))
        .order_by(Site.name)
    )
    return db.scalars(stmt).all()


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned(db, Site, site_id, company_id_of(user))


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(body: SiteCreate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    site = Site(
        company_id=company_id_of(user),
        name=body.name,
        site_type=body.site_type,
        address=body.address,
        safety_threshold=body.safety_threshold,
    )
    required = set(body.required_ppe) if body.required_ppe else DEFAULT_REQUIRED[body.site_type]
    for item in PpeItem:
        site.rules.append(PpeRule(ppe_item=item, is_required=item in required, severity=DEFAULT_SEVERITY[item]))
    db.add(site)
    db.commit()
    write_audit(db, "SITE_CREATED", request, user.id, site.name)
    return site


@router.put("/{site_id}", response_model=SiteOut)
def update_site(site_id: uuid.UUID, body: SiteUpdate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    site = get_owned(db, Site, site_id, company_id_of(user))
    data = body.model_dump(exclude_unset=True)
    required = data.pop("required_ppe", None)
    for key, value in data.items():
        if value is not None or key == "address":
            setattr(site, key, value)
    if required is not None:
        wanted = set(required)
        for rule in site.rules:
            rule.is_required = rule.ppe_item in wanted
    db.commit()
    write_audit(db, "SITE_UPDATED", request, user.id, site.name)
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: uuid.UUID, request: Request, user: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    site = get_owned(db, Site, site_id, company_id_of(user))
    name = site.name
    db.delete(site)
    db.commit()
    write_audit(db, "SITE_DELETED", request, user.id, name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

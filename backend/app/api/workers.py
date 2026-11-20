import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import ADMINS, WRITERS, company_id_of, get_current_user, get_owned, require_roles
from app.database.session import get_db
from app.models import Site, User, Worker
from app.schemas.resources import WorkerCreate, WorkerOut, WorkerUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/api/workers", tags=["workers"])


def _code_taken(db: Session, cid: uuid.UUID, code: str, exclude: uuid.UUID | None = None) -> bool:
    found = db.scalar(select(Worker.id).where(Worker.company_id == cid, Worker.employee_code == code))
    return found is not None and found != exclude


@router.get("", response_model=list[WorkerOut])
def list_workers(
    search: str | None = Query(default=None, max_length=100),
    site_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Worker).where(Worker.company_id == company_id_of(user)).options(selectinload(Worker.site)).order_by(Worker.full_name)
    if site_id:
        stmt = stmt.where(Worker.site_id == site_id)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Worker.full_name.ilike(like), Worker.employee_code.ilike(like)))
    return db.scalars(stmt).all()


@router.post("", response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def create_worker(body: WorkerCreate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    cid = company_id_of(user)
    if body.site_id:
        get_owned(db, Site, body.site_id, cid)
    if _code_taken(db, cid, body.employee_code):
        raise HTTPException(status.HTTP_409_CONFLICT, "A worker with this employee code already exists")
    worker = Worker(company_id=cid, **body.model_dump())
    db.add(worker)
    db.commit()
    write_audit(db, "WORKER_CREATED", request, user.id, worker.full_name)
    return worker


@router.put("/{worker_id}", response_model=WorkerOut)
def update_worker(worker_id: uuid.UUID, body: WorkerUpdate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    cid = company_id_of(user)
    worker = get_owned(db, Worker, worker_id, cid)
    data = body.model_dump(exclude_unset=True)
    if data.get("site_id"):
        get_owned(db, Site, data["site_id"], cid)
    if data.get("employee_code") and _code_taken(db, cid, data["employee_code"], exclude=worker.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "A worker with this employee code already exists")
    for key, value in data.items():
        if value is not None or key in ("site_id", "department"):
            setattr(worker, key, value)
    db.commit()
    write_audit(db, "WORKER_UPDATED", request, user.id, worker.full_name)
    return worker


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: uuid.UUID, request: Request, user: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    worker = get_owned(db, Worker, worker_id, company_id_of(user))
    name = worker.full_name
    db.delete(worker)
    db.commit()
    write_audit(db, "WORKER_DELETED", request, user.id, name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import ADMINS, WRITERS, company_id_of, get_current_user, get_owned, require_roles
from app.database.session import get_db
from app.models import Camera, CameraStatus, Site, SourceType, User
from app.schemas.resources import CameraCreate, CameraOut, CameraUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


def _code_taken(db: Session, cid: uuid.UUID, code: str, exclude: uuid.UUID | None = None) -> bool:
    stmt = select(Camera.id).where(Camera.company_id == cid, Camera.camera_code == code)
    found = db.scalar(stmt)
    return found is not None and found != exclude


@router.get("", response_model=list[CameraOut])
def list_cameras(site_id: uuid.UUID | None = None, status_filter: CameraStatus | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Camera).where(Camera.company_id == company_id_of(user)).options(selectinload(Camera.site)).order_by(Camera.name)
    if site_id:
        stmt = stmt.where(Camera.site_id == site_id)
    if status_filter:
        stmt = stmt.where(Camera.status == status_filter)
    return db.scalars(stmt).all()


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned(db, Camera, camera_id, company_id_of(user))


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(body: CameraCreate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    cid = company_id_of(user)
    get_owned(db, Site, body.site_id, cid)
    if _code_taken(db, cid, body.camera_code):
        raise HTTPException(status.HTTP_409_CONFLICT, "A camera with this camera ID already exists")
    camera = Camera(company_id=cid, **body.model_dump())
    if camera.status == CameraStatus.ONLINE:
        camera.last_active_at = datetime.now(timezone.utc)
    db.add(camera)
    db.commit()
    write_audit(db, "CAMERA_CREATED", request, user.id, camera.name)
    return camera


@router.put("/{camera_id}", response_model=CameraOut)
def update_camera(camera_id: uuid.UUID, body: CameraUpdate, request: Request, user: User = Depends(require_roles(*WRITERS)), db: Session = Depends(get_db)):
    cid = company_id_of(user)
    camera = get_owned(db, Camera, camera_id, cid)
    data = body.model_dump(exclude_unset=True)
    if data.get("site_id"):
        get_owned(db, Site, data["site_id"], cid)
    if data.get("camera_code") and _code_taken(db, cid, data["camera_code"], exclude=camera.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "A camera with this camera ID already exists")
    for key, value in data.items():
        if value is not None or key in ("location", "stream_url"):
            setattr(camera, key, value)
    if camera.source_type == SourceType.RTSP and not (camera.stream_url or "").lower().startswith(("rtsp://", "rtsps://")):
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "RTSP cameras need a stream URL starting with rtsp://")
    if data.get("status") == CameraStatus.ONLINE:
        camera.last_active_at = datetime.now(timezone.utc)
    db.commit()
    write_audit(db, "CAMERA_UPDATED", request, user.id, camera.name)
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: uuid.UUID, request: Request, user: User = Depends(require_roles(*ADMINS)), db: Session = Depends(get_db)):
    camera = get_owned(db, Camera, camera_id, company_id_of(user))
    name = camera.name
    db.delete(camera)
    db.commit()
    write_audit(db, "CAMERA_DELETED", request, user.id, name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

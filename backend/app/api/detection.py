import base64
import logging
import re
import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import WRITERS, company_id_of, get_current_user, get_owned, require_roles
from app.core.config import get_settings
from app.database.session import get_db
from app.ml import postprocessing
from app.ml.model_loader import ModelUnavailable, model_status
from app.models import DetectionJob, JobStatus, Site, User
from app.schemas.resources import JobOut
from app.services import detection_service as svc
from app.services.audit import write_audit
from app.services.video_processing import probe_video
from app.workers.video_job import run_video_job

router = APIRouter(prefix="/api/detection", tags=["detection"])
log = logging.getLogger("safevision.detection")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}
CHUNK = 1024 * 1024
MODEL_HELP = "AI model is not available."


def _ext(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _display_name(filename: str | None) -> str:
    """Cosmetic only: the file is stored under a random name, never the uploaded one."""
    return re.sub(r"[^\w.\- ]", "_", Path(filename or "video").name)[:200] or "video"


def _unavailable(exc: ModelUnavailable) -> HTTPException:
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc) or MODEL_HELP)


@router.get("/status")
def detection_status(_: User = Depends(get_current_user)):
    return model_status()


@router.post("/image")
def detect_image(
    file: UploadFile = File(...),
    site_id: uuid.UUID | None = Form(default=None),
    user: User = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
):
    if _ext(file.filename) not in IMAGE_EXTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image format. Use JPG, PNG or WEBP.")
    limit = get_settings().IMAGE_MAX_MB * CHUNK
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Image is larger than {get_settings().IMAGE_MAX_MB} MB.")
    rules = svc.load_rules(db, company_id_of(user), site_id)
    try:
        frame, persons, ppe = svc.analyze_bytes(data, rules)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image format. The file could not be read.")
    except ModelUnavailable as exc:
        raise _unavailable(exc)
    annotated = postprocessing.annotate(frame, persons, ppe)
    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
    payload = svc.result_payload(frame, persons, ppe)
    payload["image"] = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
    return payload


@router.post("/video", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def upload_video(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    site_id: uuid.UUID | None = Form(default=None),
    user: User = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
):
    s = get_settings()
    ext = _ext(file.filename)
    if ext not in VIDEO_EXTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid video format. Use MP4, AVI, MOV or MKV.")
    cid = company_id_of(user)
    if site_id:
        get_owned(db, Site, site_id, cid)

    job_id = uuid.uuid4()
    upload_dir = Path(s.UPLOAD_DIR) / "videos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{job_id}{ext}"
    limit, written = s.VIDEO_MAX_MB * CHUNK, 0
    try:
        with open(path, "wb") as out:
            while chunk := file.file.read(CHUNK):
                written += len(chunk)
                if written > limit:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Video is larger than {s.VIDEO_MAX_MB} MB.")
                out.write(chunk)
        try:
            probe_video(str(path))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid video format. The file could not be read.")
    except HTTPException:
        path.unlink(missing_ok=True)
        raise

    job = DetectionJob(id=job_id, company_id=cid, site_id=site_id, user_id=user.id,
                       original_name=_display_name(file.filename), input_path=str(path))
    db.add(job)
    db.commit()
    write_audit(db, "VIDEO_UPLOADED", request, user.id, job.original_name)
    background.add_task(run_video_job, job.id)
    return job


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(DetectionJob).where(DetectionJob.company_id == company_id_of(user)).order_by(DetectionJob.created_at.desc()).limit(30)
    return db.scalars(stmt).all()


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned(db, DetectionJob, job_id, company_id_of(user))


@router.get("/jobs/{job_id}/video")
def download_video(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = get_owned(db, DetectionJob, job_id, company_id_of(user))
    if job.status != JobStatus.COMPLETED or not job.output_path or not Path(job.output_path).is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Processed video is not available")
    return FileResponse(job.output_path, media_type="video/mp4", filename=f"{Path(job.original_name).stem}-processed.mp4")

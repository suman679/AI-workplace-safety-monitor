import logging
from pathlib import Path

from app.database.session import SessionLocal
from app.ml.model_loader import ModelUnavailable
from app.models import DetectionJob, JobStatus
from app.services.detection_service import load_rules
from app.services.video_processing import process_video

log = logging.getLogger("safevision.jobs")


def run_video_job(job_id, session_factory=SessionLocal) -> None:
    """Runs in a background thread so the upload request returns immediately."""
    db = session_factory()
    try:
        job = db.get(DetectionJob, job_id)
        if job is None:
            return
        job.status, job.progress = JobStatus.PROCESSING, 0.0
        db.commit()
        try:
            rules = load_rules(db, job.company_id, job.site_id)
            out = str(Path(job.input_path).parent.parent / "processed" / f"{job.id}.mp4")
            Path(out).parent.mkdir(parents=True, exist_ok=True)

            def on_progress(pct: float):
                job.progress = pct
                db.commit()

            summary = process_video(job.input_path, out, rules, on_progress)
            job.summary, job.output_path, job.progress, job.status = summary, out, 100.0, JobStatus.COMPLETED
        except ModelUnavailable as exc:
            job.status, job.error = JobStatus.FAILED, str(exc)[:300]
        except Exception:
            log.exception("Video job %s failed", job_id)
            db.rollback()
            job = db.get(DetectionJob, job_id)
            job.status, job.error = JobStatus.FAILED, "Video processing failed."
        db.commit()
    finally:
        db.close()

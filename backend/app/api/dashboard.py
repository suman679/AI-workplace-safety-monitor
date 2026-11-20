from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import company_id_of, get_current_user
from app.database.session import get_db
from app.models import Camera, CameraStatus, Site, User, Worker
from app.schemas.resources import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cid = company_id_of(user)
    count = lambda col, *where: db.scalar(select(func.count(col)).where(*where)) or 0  # noqa: E731
    by_status = {s.value: 0 for s in CameraStatus}
    for st, n in db.execute(select(Camera.status, func.count(Camera.id)).where(Camera.company_id == cid).group_by(Camera.status)):
        by_status[st.value] = n
    return DashboardStats(
        total_sites=count(Site.id, Site.company_id == cid),
        total_cameras=sum(by_status.values()),
        online_cameras=by_status["ONLINE"],
        total_workers=count(Worker.id, Worker.company_id == cid),
        active_workers=count(Worker.id, Worker.company_id == cid, Worker.is_active.is_(True)),
        cameras_by_status=by_status,
    )

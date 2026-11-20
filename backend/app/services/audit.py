import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(db: Session, action: str, request: Request, user_id: uuid.UUID | None = None, detail: str | None = None):
    ip = request.client.host if request.client else None
    db.add(AuditLog(user_id=user_id, action=action, ip_address=ip, detail=detail))
    db.commit()

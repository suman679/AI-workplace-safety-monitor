import logging
import uuid
from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import WRITERS
from app.core.security import decode_token
from app.database.session import get_db
from app.ml.model_loader import ModelUnavailable
from app.ml.tracker import Tracker
from app.models import Camera, CameraStatus, User
from app.services import detection_service as svc

router = APIRouter(tags=["realtime"])
log = logging.getLogger("safevision.realtime")
MAX_FRAME_BYTES = 2 * 1024 * 1024


def _process(data: bytes, rules, tracker) -> dict:
    frame, persons, ppe = svc.analyze_bytes(data, rules, tracker)
    return svc.result_payload(frame, persons, ppe)


async def _reject(ws: WebSocket, code: int, message: str):
    await ws.send_json({"error": message})
    await ws.close(code)


@router.websocket("/ws/detect")
async def ws_detect(
    ws: WebSocket,
    token: str,
    site_id: uuid.UUID | None = None,
    camera_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    """Browser sends one JPEG per message and waits for the JSON result before sending the next (natural backpressure)."""
    await ws.accept()
    try:
        user = db.get(User, uuid.UUID(decode_token(token, "access")["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        return await _reject(ws, 4401, "Authentication expired")
    if user is None or not user.is_active or user.company_id is None:
        return await _reject(ws, 4401, "Authentication expired")
    if user.role not in WRITERS and user.role.value != "SUPER_ADMIN":
        return await _reject(ws, 4403, "Your role cannot run live monitoring")
    try:
        rules = svc.load_rules(db, user.company_id, site_id)
        camera = db.get(Camera, camera_id) if camera_id else None
        if camera_id and (camera is None or camera.company_id != user.company_id):
            return await _reject(ws, 4404, "Camera not found")
    except Exception:
        return await _reject(ws, 4404, "Site not found")

    def set_status(value: CameraStatus):
        if camera:
            camera.status = value
            if value == CameraStatus.ONLINE:
                camera.last_active_at = datetime.now(timezone.utc)
            db.commit()

    set_status(CameraStatus.ONLINE)
    tracker = Tracker()
    try:
        while True:
            data = await ws.receive_bytes()
            if len(data) > MAX_FRAME_BYTES:
                await ws.send_json({"error": "Frame too large"})
                continue
            try:
                await ws.send_json(await run_in_threadpool(_process, data, rules, tracker))
            except ValueError:
                await ws.send_json({"error": "Invalid frame"})
    except WebSocketDisconnect:
        pass
    except ModelUnavailable as exc:
        await _reject(ws, 4503, str(exc))
    except Exception:
        log.exception("Live detection failed")
        await _reject(ws, 1011, "Live detection failed")
    finally:
        set_status(CameraStatus.OFFLINE)

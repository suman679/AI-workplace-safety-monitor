import types
import uuid

import cv2
import numpy as np
import pytest

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import get_db
from app.main import app as fastapi_app
from app.ml.detector import Detection
from app.ml.model_loader import ModelUnavailable
from app.models import Role, User
from app.models.enums import PpeItem
from app.services import detection_service as svc
from app.workers.video_job import run_video_job

H, V = PpeItem.HELMET, PpeItem.VEST
FAKE_MODEL = types.SimpleNamespace(support={H: "positive", V: "positive"}, ppe_capable=True)


def jpeg(w=320, h=240) -> bytes:
    ok, buf = cv2.imencode(".jpg", np.full((h, w, 3), 90, np.uint8))
    return buf.tobytes()


def make_video(path, frames=12, w=320, h=240):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w, h))
    for i in range(frames):
        writer.write(np.full((h, w, 3), 40 + i, np.uint8))
    writer.release()
    return path


@pytest.fixture(autouse=True)
def fake_ai(monkeypatch, tmp_path):
    """No torch needed: one worker wearing a helmet but no vest."""
    state = {"detections": [
        Detection("person", None, (100, 40, 200, 220), 0.92, "person"),
        Detection("has", H, (120, 30, 180, 90), 0.88, "helmet"),
    ]}
    monkeypatch.setattr(svc, "detect", lambda frame: list(state["detections"]))
    monkeypatch.setattr(svc, "get_model", lambda: FAKE_MODEL)
    monkeypatch.setattr(get_settings(), "UPLOAD_DIR", str(tmp_path))
    return state


def register(client, email="a@acme.com", company="Acme"):
    r = client.post("/api/auth/register", json={"full_name": "Admin User", "email": email, "password": "Safety123", "company_name": company})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()


def post_image(client, h, data=None, name="site.jpg", **form):
    return client.post("/api/detection/image", headers=h, files={"file": (name, data or jpeg(), "image/jpeg")}, data=form)


def test_image_detection_response_format(client):
    h, _ = register(client)
    r = post_image(client, h)
    assert r.status_code == 200
    body = r.json()
    p = body["persons"][0]
    assert p["helmet"] is True and p["vest"] is False and p["gloves"] is None
    assert p["violations"] == ["Missing Vest"] and p["state"] == "VIOLATION" and p["compliance_score"] == 50.0
    assert body["summary"]["workers"] == 1 and body["summary"]["violations"] == 1
    assert body["image"].startswith("data:image/jpeg;base64,") and body["ppe_capable"] is True


def test_image_uses_the_sites_rules(client):
    h, _ = register(client)
    site = client.post("/api/sites", json={"name": "Yard", "required_ppe": ["HELMET"]}, headers=h).json()
    r = post_image(client, h, site_id=site["id"])
    assert r.json()["persons"][0]["state"] == "SAFE"


def test_image_validation(client):
    h, _ = register(client)
    assert post_image(client, h, name="x.gif").status_code == 400
    assert post_image(client, h, data=b"not an image").status_code == 400
    assert client.post("/api/detection/image", files={"file": ("a.jpg", jpeg(), "image/jpeg")}).status_code == 401


def test_image_size_limit(client, monkeypatch):
    h, _ = register(client)
    monkeypatch.setattr(get_settings(), "IMAGE_MAX_MB", 0)
    assert post_image(client, h).status_code == 413


def test_model_unavailable_gives_503(client, monkeypatch):
    h, _ = register(client)

    def boom(frame):
        raise ModelUnavailable("AI libraries are not installed. Run: pip install -r requirements-ml.txt")

    monkeypatch.setattr(svc, "detect", boom)
    r = post_image(client, h)
    assert r.status_code == 503 and "requirements-ml.txt" in r.json()["error"]["message"]


def test_viewer_cannot_run_detection(client):
    h, data = register(client)
    db = next(fastapi_app.dependency_overrides[get_db]())
    db.add(User(company_id=uuid.UUID(data["user"]["company_id"]), full_name="Viewer", email="v@acme.com", hashed_password=hash_password("Viewer123"), role=Role.VIEWER))
    db.commit()
    tok = client.post("/api/auth/login", json={"email": "v@acme.com", "password": "Viewer123"}).json()["access_token"]
    assert post_image(client, {"Authorization": f"Bearer {tok}"}).status_code == 403


def test_status_endpoint_does_not_load_the_model(client):
    h, _ = register(client)
    body = client.get("/api/detection/status", headers=h).json()
    assert {"ml_installed", "loaded", "ppe_capable", "confidence_threshold"} <= body.keys()


def test_video_job_end_to_end(client, monkeypatch, tmp_path):
    h, _ = register(client)
    monkeypatch.setattr("app.api.detection.run_video_job", lambda job_id: run_video_job(job_id, session_factory=client.Session))
    video = make_video(tmp_path / "in.mp4")
    with open(video, "rb") as f:
        r = client.post("/api/detection/video", headers=h, files={"file": ("../../evil name.mp4", f, "video/mp4")})
    assert r.status_code == 202, r.text
    job_id = r.json()["id"]
    assert "evil" in r.json()["original_name"] and "/" not in r.json()["original_name"]

    job = client.get(f"/api/detection/jobs/{job_id}", headers=h).json()
    assert job["status"] == "COMPLETED", job
    s = job["summary"]
    assert s["total_workers"] == 1 and s["workers_with_violations"] == 1
    assert s["violations_by_item"]["VEST"] == 1 and s["violations_by_item"]["HELMET"] == 0
    assert s["compliance_rate"] == 0.0 and s["safety_score"] == 50.0 and s["ppe_checked"] is True

    dl = client.get(f"/api/detection/jobs/{job_id}/video", headers=h)
    assert dl.status_code == 200 and dl.headers["content-type"] == "video/mp4" and len(dl.content) > 500
    assert len(client.get("/api/detection/jobs", headers=h).json()) == 1

    other, _ = register(client, "b@rival.com", "Rival")
    assert client.get(f"/api/detection/jobs/{job_id}", headers=other).status_code == 404
    assert client.get(f"/api/detection/jobs/{job_id}/video", headers=other).status_code == 404


def test_video_validation(client, tmp_path):
    h, _ = register(client)
    assert client.post("/api/detection/video", headers=h, files={"file": ("a.txt", b"hello", "text/plain")}).status_code == 400
    bad = client.post("/api/detection/video", headers=h, files={"file": ("a.mp4", b"not really a video", "video/mp4")})
    assert bad.status_code == 400 and "Invalid video format" in bad.json()["error"]["message"]
    assert not list((tmp_path / "videos").glob("*"))  # rejected upload is not kept on disk


def test_video_job_failure_is_reported(client, monkeypatch, tmp_path):
    h, _ = register(client)
    monkeypatch.setattr("app.api.detection.run_video_job", lambda job_id: run_video_job(job_id, session_factory=client.Session))

    def boom(frame):
        raise ModelUnavailable("AI libraries are not installed.")

    monkeypatch.setattr(svc, "detect", boom)
    video = make_video(tmp_path / "in.mp4")
    with open(video, "rb") as f:
        job_id = client.post("/api/detection/video", headers=h, files={"file": ("a.mp4", f, "video/mp4")}).json()["id"]
    job = client.get(f"/api/detection/jobs/{job_id}", headers=h).json()
    assert job["status"] == "FAILED" and "not installed" in job["error"]


def test_websocket_live_detection_and_camera_status(client):
    h, _ = register(client)
    site = client.post("/api/sites", json={"name": "Yard"}, headers=h).json()
    cam = client.post("/api/cameras", json={"name": "Webcam 1", "camera_code": "W1", "site_id": site["id"]}, headers=h).json()
    token = h["Authorization"].split()[1]
    with client.websocket_connect(f"/ws/detect?token={token}&site_id={site['id']}&camera_id={cam['id']}") as ws:
        ws.send_bytes(jpeg())
        msg = ws.receive_json()
        assert msg["persons"][0]["person_id"] == 1 and msg["summary"]["workers"] == 1
        ws.send_bytes(b"garbage")
        assert ws.receive_json()["error"] == "Invalid frame"
        ws.send_bytes(jpeg())
        assert ws.receive_json()["persons"][0]["person_id"] == 1  # tracker keeps the same id
        assert client.get(f"/api/cameras/{cam['id']}", headers=h).json()["status"] == "ONLINE"
    assert client.get(f"/api/cameras/{cam['id']}", headers=h).json()["status"] == "OFFLINE"


def test_websocket_rejects_bad_token(client):
    with client.websocket_connect("/ws/detect?token=nope") as ws:
        assert ws.receive_json()["error"] == "Authentication expired"

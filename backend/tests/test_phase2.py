import uuid

import pytest

from app.core.security import hash_password
from app.database.session import get_db
from app.main import app as fastapi_app
from app.models import Role, User


def register(client, email="admin@acme.com", company="Acme"):
    r = client.post("/api/auth/register", json={"full_name": "Admin User", "email": email, "password": "Safety123", "company_name": company})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]


def make_viewer(client, admin_user):
    db = next(fastapi_app.dependency_overrides[get_db]())
    db.add(User(company_id=uuid.UUID(admin_user["company_id"]), full_name="View Only", email="viewer@acme.com",
                hashed_password=hash_password("Viewer123"), role=Role.VIEWER))
    db.commit()
    r = client.post("/api/auth/login", json={"email": "viewer@acme.com", "password": "Viewer123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin(client):
    headers, user = register(client)
    return headers, user


def new_site(client, h, **over):
    body = {"name": "Site A", "site_type": "CONSTRUCTION", **over}
    r = client.post("/api/sites", json=body, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_site_gets_default_rules_for_its_type(client, admin):
    h, _ = admin
    assert new_site(client, h)["required_ppe"] == ["HELMET", "VEST", "SAFETY_SHOES"]
    factory = new_site(client, h, name="Plant 1", site_type="FACTORY")
    assert factory["required_ppe"] == ["HELMET", "GLOVES", "SAFETY_SHOES"]


def test_site_custom_ppe_and_update(client, admin):
    h, _ = admin
    site = new_site(client, h, required_ppe=["MASK", "GLOVES"])
    assert site["required_ppe"] == ["GLOVES", "MASK"]
    r = client.put(f"/api/sites/{site['id']}", json={"required_ppe": ["HELMET"], "safety_threshold": 90}, headers=h)
    assert r.json()["required_ppe"] == ["HELMET"] and r.json()["safety_threshold"] == 90
    rules = client.get(f"/api/ppe-rules?site_id={site['id']}", headers=h).json()
    assert len(rules) == 5 and [x["ppe_item"] for x in rules if x["is_required"]] == ["HELMET"]


def test_rule_severity_update(client, admin):
    h, _ = admin
    site = new_site(client, h)
    rule = client.get(f"/api/ppe-rules?site_id={site['id']}", headers=h).json()[0]
    r = client.put(f"/api/ppe-rules/{rule['id']}", json={"severity": "CRITICAL", "is_required": False}, headers=h)
    assert r.status_code == 200 and r.json()["severity"] == "CRITICAL" and r.json()["is_required"] is False


def test_viewer_can_read_but_not_write(client, admin):
    h, user = admin
    site = new_site(client, h)
    v = make_viewer(client, user)
    assert client.get("/api/sites", headers=v).status_code == 200
    assert client.post("/api/sites", json={"name": "Nope"}, headers=v).status_code == 403
    assert client.delete(f"/api/sites/{site['id']}", headers=v).status_code == 403
    assert client.get("/api/sites").status_code == 401


def test_companies_are_isolated(client, admin):
    h, _ = admin
    site = new_site(client, h)
    other, _ = register(client, "boss@rival.com", "Rival")
    assert client.get("/api/sites", headers=other).json() == []
    assert client.get(f"/api/sites/{site['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/sites/{site['id']}", headers=other).status_code == 404
    assert client.post("/api/cameras", json={"name": "Cam", "camera_code": "C1", "site_id": site["id"]}, headers=other).status_code == 404


def test_camera_crud_and_validation(client, admin):
    h, _ = admin
    site = new_site(client, h)
    base = {"name": "Gate Cam", "camera_code": "CAM-01", "site_id": site["id"], "location": "Main gate"}
    r = client.post("/api/cameras", json={**base, "status": "ONLINE"}, headers=h)
    assert r.status_code == 201
    cam = r.json()
    assert cam["site_name"] == "Site A" and cam["last_active_at"] is not None
    assert client.post("/api/cameras", json=base, headers=h).status_code == 409
    bad = client.post("/api/cameras", json={**base, "camera_code": "CAM-02", "source_type": "RTSP"}, headers=h)
    assert bad.status_code == 422
    ok = client.post("/api/cameras", json={**base, "camera_code": "CAM-03", "source_type": "RTSP", "stream_url": "rtsp://10.0.0.5/live"}, headers=h)
    assert ok.status_code == 201
    upd = client.put(f"/api/cameras/{cam['id']}", json={"status": "WARNING"}, headers=h)
    assert upd.json()["status"] == "WARNING"
    assert len(client.get(f"/api/cameras?site_id={site['id']}", headers=h).json()) == 2
    assert client.delete(f"/api/cameras/{cam['id']}", headers=h).status_code == 204


def test_worker_crud_search_and_duplicates(client, admin):
    h, _ = admin
    site = new_site(client, h)
    body = {"employee_code": "E-100", "full_name": "Ravi Kumar", "site_id": site["id"], "department": "Welding"}
    w = client.post("/api/workers", json=body, headers=h)
    assert w.status_code == 201 and w.json()["site_name"] == "Site A"
    assert client.post("/api/workers", json=body, headers=h).status_code == 409
    client.post("/api/workers", json={"employee_code": "E-200", "full_name": "Meena Devi"}, headers=h)
    assert [x["full_name"] for x in client.get("/api/workers?search=ravi", headers=h).json()] == ["Ravi Kumar"]
    assert len(client.get(f"/api/workers?site_id={site['id']}", headers=h).json()) == 1
    r = client.put(f"/api/workers/{w.json()['id']}", json={"site_id": None, "is_active": False}, headers=h)
    assert r.json()["site_id"] is None and r.json()["is_active"] is False


def test_dashboard_stats_use_real_data(client, admin):
    h, _ = admin
    assert client.get("/api/dashboard/stats", headers=h).json()["total_sites"] == 0
    site = new_site(client, h)
    client.post("/api/cameras", json={"name": "Cam A", "camera_code": "1", "site_id": site["id"], "status": "ONLINE"}, headers=h)
    client.post("/api/cameras", json={"name": "Cam B", "camera_code": "2", "site_id": site["id"]}, headers=h)
    client.post("/api/workers", json={"employee_code": "1", "full_name": "Worker One"}, headers=h)
    client.post("/api/workers", json={"employee_code": "2", "full_name": "Worker Two", "is_active": False}, headers=h)
    s = client.get("/api/dashboard/stats", headers=h).json()
    assert (s["total_sites"], s["total_cameras"], s["online_cameras"]) == (1, 2, 1)
    assert (s["total_workers"], s["active_workers"]) == (2, 1)
    assert s["cameras_by_status"] == {"ONLINE": 1, "OFFLINE": 1, "WARNING": 0}


def test_deleting_a_site_removes_its_cameras_and_unassigns_workers(client, admin):
    h, _ = admin
    site = new_site(client, h)
    assert client.post("/api/cameras", json={"name": "Cam A", "camera_code": "1", "site_id": site["id"]}, headers=h).status_code == 201
    w = client.post("/api/workers", json={"employee_code": "1", "full_name": "Worker One", "site_id": site["id"]}, headers=h).json()
    assert client.delete(f"/api/sites/{site['id']}", headers=h).status_code == 204
    assert client.get("/api/cameras", headers=h).json() == []
    assert client.get("/api/workers", headers=h).json()[0]["site_id"] is None

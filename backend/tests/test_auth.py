REG = {"full_name": "Asha Rao", "email": "asha@example.com", "password": "Safety123", "company_name": "Acme Build"}


def register(client, **over):
    return client.post("/api/auth/register", json={**REG, **over})


def test_register_returns_tokens_and_admin_role(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["role"] == "COMPANY_ADMIN"
    assert "hashed_password" not in body["user"]
    assert body["access_token"] and body["refresh_token"]


def test_duplicate_email_conflict(client):
    register(client)
    assert register(client, email="ASHA@example.com").status_code == 409


def test_weak_password_rejected(client):
    r = register(client, password="onlyletters")
    assert r.status_code == 422
    assert r.json()["error"]["message"] == "Validation failed"


def test_login_success_and_failure(client):
    register(client)
    ok = client.post("/api/auth/login", json={"email": REG["email"], "password": REG["password"]})
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={"email": REG["email"], "password": "wrong-pass1"})
    assert bad.status_code == 401
    unknown = client.post("/api/auth/login", json={"email": "no@one.com", "password": "wrong-pass1"})
    assert unknown.json() == bad.json()


def test_me_requires_valid_access_token(client):
    assert client.get("/api/auth/me").status_code == 401
    tokens = register(client).json()
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/auth/me", headers=h).json()["email"] == REG["email"]
    # a refresh token must not work as an access token
    bad = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert client.get("/api/auth/me", headers=bad).status_code == 401


def test_refresh_flow(client):
    tokens = register(client).json()
    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": "garbage"}).status_code == 401


def test_password_reset_is_single_use(client):
    from app.core.security import create_reset_token
    from app.models.user import User

    tokens = register(client).json()
    from app.database.session import get_db
    from app.main import app as fastapi_app

    db = next(fastapi_app.dependency_overrides[get_db]())
    user = db.query(User).one()
    token = create_reset_token(str(user.id), user.hashed_password)
    ok = client.post("/api/auth/reset-password", json={"token": token, "new_password": "NewSafety456"})
    assert ok.status_code == 200
    again = client.post("/api/auth/reset-password", json={"token": token, "new_password": "Another789x"})
    assert again.status_code == 400
    login = client.post("/api/auth/login", json={"email": REG["email"], "password": "NewSafety456"})
    assert login.status_code == 200


def test_forgot_password_does_not_reveal_accounts(client):
    r = client.post("/api/auth/forgot-password", json={"email": "ghost@example.com"})
    assert r.status_code == 200

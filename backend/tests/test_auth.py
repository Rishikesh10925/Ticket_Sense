def test_register_creates_end_user(api):
    resp = api.post(
        "/auth/register",
        json={"email": "alice@example.com", "full_name": "Alice", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "end_user"
    assert body["email"] == "alice@example.com"


def test_register_duplicate_email_conflicts(api):
    payload = {"email": "bob@example.com", "full_name": "Bob", "password": "password123"}
    assert api.post("/auth/register", json=payload).status_code == 201
    assert api.post("/auth/register", json=payload).status_code == 409


def test_login_success_returns_token(api):
    api.post(
        "/auth/register",
        json={"email": "carol@example.com", "full_name": "Carol", "password": "password123"},
    )
    resp = api.post(
        "/auth/login", data={"username": "carol@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


def test_login_wrong_password_401(api):
    api.post(
        "/auth/register",
        json={"email": "dave@example.com", "full_name": "Dave", "password": "password123"},
    )
    resp = api.post("/auth/login", data={"username": "dave@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_token(api):
    assert api.get("/auth/me").status_code == 401

    api.post(
        "/auth/register",
        json={"email": "erin@example.com", "full_name": "Erin", "password": "password123"},
    )
    token = api.post(
        "/auth/login", data={"username": "erin@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "erin@example.com"

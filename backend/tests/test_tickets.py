import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, User


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _create_user_sync(email: str, role: str, department_name: str | None = None) -> None:
    # Self-contained engine within this asyncio.run() call — see conftest.py's
    # _truncate() for why the app's shared engine can't be reused here.
    async def _create():
        setup_engine = create_async_engine(settings.database_url)
        setup_session = async_sessionmaker(setup_engine, expire_on_commit=False)
        async with setup_session() as db:
            department_id = None
            if department_name:
                dept = Department(name=department_name)
                db.add(dept)
                await db.flush()
                department_id = dept.id
            db.add(
                User(
                    email=email,
                    full_name="Test",
                    role=role,
                    department_id=department_id,
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await setup_engine.dispose()

    asyncio.run(_create())


def _login(api, email: str) -> str:
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def test_create_ticket_requires_auth(api):
    resp = api.post("/tickets", data={"subject": "x", "description": "y"})
    assert resp.status_code == 401


def test_create_and_get_ticket(api):
    token = _register_and_login(api, "frank@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = api.post(
        "/tickets", data={"subject": "VPN broken", "description": "Can't connect"}, headers=headers
    )
    assert create_resp.status_code == 201
    ticket = create_resp.json()
    assert ticket["status"] == "submitted"
    assert ticket["subject"] == "VPN broken"

    get_resp = api.get(f"/tickets/{ticket['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ticket["id"]


def test_end_user_only_sees_own_tickets(api):
    token_a = _register_and_login(api, "grace@example.com")
    token_b = _register_and_login(api, "henry@example.com")

    api.post(
        "/tickets",
        data={"subject": "A's ticket", "description": "..."},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    resp = api.get("/tickets", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    assert resp.json() == []

    resp = api.get("/tickets", headers={"Authorization": f"Bearer {token_a}"})
    assert len(resp.json()) == 1


def test_engineer_cannot_see_ticket_outside_own_department(api):
    end_user_token = _register_and_login(api, "iris@example.com")
    create_resp = api.post(
        "/tickets",
        data={"subject": "Unrouted ticket", "description": "..."},
        headers={"Authorization": f"Bearer {end_user_token}"},
    )
    ticket_id = create_resp.json()["id"]

    _create_user_sync("engineer@example.com", "department_engineer", department_name="Networking")
    engineer_token = _login(api, "engineer@example.com")

    resp = api.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {engineer_token}"})
    assert resp.status_code == 403


def test_admin_sees_all_tickets(api):
    end_user_token = _register_and_login(api, "jack@example.com")
    api.post(
        "/tickets",
        data={"subject": "Some ticket", "description": "..."},
        headers={"Authorization": f"Bearer {end_user_token}"},
    )

    _create_user_sync("admin@example.com", "admin")
    admin_token = _login(api, "admin@example.com")

    resp = api.get("/tickets", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

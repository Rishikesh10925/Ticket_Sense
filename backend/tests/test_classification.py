import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Department


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _department_id_sync(name: str) -> str:
    # TestClient's background task (see conftest.py) runs the classifier against
    # whatever Department rows exist, so tests need real department rows, not just
    # a name string, to compare against.
    async def _get():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            dept = await db.scalar(select(Department).where(Department.name == name))
            if dept is None:
                dept = Department(name=name)
                db.add(dept)
                await db.commit()
                await db.refresh(dept)
            result = str(dept.id)
        await engine.dispose()
        return result

    return asyncio.run(_get())


def test_ticket_auto_classified_and_routed(api):
    networking_id = _department_id_sync("Networking")
    token = _register_and_login(api, "kim@example.com")

    resp = api.post(
        "/tickets",
        data={
            "subject": "VPN not connecting from home",
            "description": "My VPN client hangs on connecting and never gets in, need this fixed today",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    created = resp.json()
    assert created["status"] == "submitted"  # the create response is serialized before
    # the background task runs — see app/routers/tickets.py. A follow-up GET reflects
    # the classification, since TestClient runs background tasks before the *next*
    # request rather than before this one's response body is built.
    ticket = api.get(f"/tickets/{created['id']}", headers={"Authorization": f"Bearer {token}"}).json()
    assert ticket["status"] == "routed"
    assert ticket["department_id"] == networking_id
    assert ticket["priority"] in ("low", "medium", "high")
    assert ticket["sentiment"] in ("positive", "neutral", "negative")


def test_queue_sort_by_priority(api):
    _department_id_sync("Networking")
    token = _register_and_login(api, "liam@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    api.post(
        "/tickets",
        data={
            "subject": "Minor wifi flicker",
            "description": "Noticing a bit of lag on wifi today, nothing major, just mentioning it.",
        },
        headers=headers,
    )
    api.post(
        "/tickets",
        data={
            "subject": "VPN down, blocking client call",
            "description": "VPN hangs on connecting, I need this fixed immediately for a client call.",
        },
        headers=headers,
    )

    resp = api.get("/tickets?sort=priority", headers=headers)
    priorities = [t["priority"] for t in resp.json()]
    rank = {"high": 3, "medium": 2, "low": 1, None: 0}
    assert priorities == sorted(priorities, key=lambda p: rank[p], reverse=True)


def test_admin_filters_queue_by_department(api):
    hr_id = _department_id_sync("HR")
    networking_id = _department_id_sync("Networking")
    end_user_token = _register_and_login(api, "mia@example.com")

    api.post(
        "/tickets",
        data={
            "subject": "How do I submit a leave request?",
            "description": "First time requesting time off, could someone point me to the leave request process?",
        },
        headers={"Authorization": f"Bearer {end_user_token}"},
    )

    admin_token = _register_and_login(api, "noah_admin@example.com")
    # register always creates an end_user — promote directly for this test.
    async def _promote():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            from app.models import User

            user = await db.scalar(select(User).where(User.email == "noah_admin@example.com"))
            user.role = "admin"
            await db.commit()
        await engine.dispose()

    asyncio.run(_promote())
    admin_token = api.post(
        "/auth/login", data={"username": "noah_admin@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.get(f"/tickets?department_id={hr_id}", headers={"Authorization": f"Bearer {admin_token}"})
    subjects = [t["subject"] for t in resp.json()]
    assert "How do I submit a leave request?" in subjects

    resp = api.get(
        f"/tickets?department_id={networking_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.json() == []

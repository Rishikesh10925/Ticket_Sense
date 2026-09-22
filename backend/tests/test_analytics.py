import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, User


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _department_id_sync(name: str) -> str:
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


def _make_engineer_sync(email: str, full_name: str, department_id: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name=full_name,
                    role="department_engineer",
                    department_id=department_id,
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def _create_admin_sync(email: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name="Admin",
                    role="admin",
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def _admin_token(api, email: str) -> str:
    _create_admin_sync(email)
    return api.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]


def _submit_ticket(api, token: str, subject: str, description: str) -> str:
    resp = api.post(
        "/tickets",
        data={"subject": subject, "description": description},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


def test_non_admin_cannot_read_analytics(api):
    token = _register_and_login(api, "analytics_enduser@example.com")
    resp = api.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_by_reviewer_reflects_real_actions_and_excludes_synthetic_placeholder(api):
    networking_id = _department_id_sync("Networking")
    admin_token = _admin_token(api, "analytics_admin@example.com")
    _make_engineer_sync("analytics_eng@example.com", "Analytics Engineer", networking_id)
    engineer_token = api.post(
        "/auth/login", data={"username": "analytics_eng@example.com", "password": "password123"}
    ).json()["access_token"]

    customer_token = _register_and_login(api, "analytics_customer@example.com")

    # One ticket accepted -> counts as "resolved".
    accepted_id = _submit_ticket(api, customer_token, "VPN not connecting", "VPN client hangs on connecting")
    ticket = api.get(f"/tickets/{accepted_id}", headers={"Authorization": f"Bearer {engineer_token}"}).json()
    assert ticket["status"] == "drafted"
    resp = api.post(
        f"/tickets/{accepted_id}/feedback",
        json={"action": "accept"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 201

    # One ticket rejected -> counts as "rejected".
    rejected_id = _submit_ticket(api, customer_token, "Wifi keeps dropping", "Wifi drops every few minutes")
    resp = api.post(
        f"/tickets/{rejected_id}/feedback",
        json={"action": "reject", "reject_reason": "Draft is wrong"},
        headers={"Authorization": f"Bearer {engineer_token}"},
    )
    assert resp.status_code == 201

    # One ticket left drafted, untouched -> counts toward "in_review" for the
    # department (not attributed to a specific reviewer, since none acted on it).
    _submit_ticket(api, customer_token, "Slow internet at desk", "My internet connection has been slow all day")

    summary = api.get("/analytics/summary", headers={"Authorization": f"Bearer {admin_token}"}).json()

    row = next(r for r in summary["by_reviewer"] if r["reviewer_email"] == "analytics_eng@example.com")
    assert row["resolved"] == 1
    assert row["rejected"] == 1
    assert row["escalated"] == 0
    assert row["in_review"] >= 1  # at least the untouched drafted ticket above

    # The synthetic bootstrap reviewer is never a row in this table — it isn't a
    # real engineer, and blending its feedback in would misattribute it to a person.
    assert all(r["reviewer_email"] != "synthetic-reviewer@ticketsense.local" for r in summary["by_reviewer"])

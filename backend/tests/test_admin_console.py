import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, KnowledgeBase, User


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _create_admin_sync(email: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name="Test Admin",
                    role="admin",
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def _seed_kb_article_sync(department_name: str, title: str) -> None:
    async def _seed():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            dept = await db.scalar(select(Department).where(Department.name == department_name))
            if dept is None:
                dept = Department(name=department_name)
                db.add(dept)
                await db.flush()
            db.add(KnowledgeBase(department_id=dept.id, title=title, content="Some content"))
            await db.commit()
        await engine.dispose()

    asyncio.run(_seed())


def test_users_list_requires_admin(api):
    token = _register_and_login(api, "priya@example.com")
    resp = api.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_sees_users_list(api):
    _register_and_login(api, "quinn@example.com")
    _create_admin_sync("admin_console@example.com")
    admin_token = api.post(
        "/auth/login", data={"username": "admin_console@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "quinn@example.com" in emails
    assert "admin_console@example.com" in emails
    # Never leak the password hash to the client.
    assert "hashed_password" not in resp.json()[0]


def test_knowledge_base_list_requires_admin(api):
    token = _register_and_login(api, "raj@example.com")
    resp = api.get("/knowledge-base", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_sees_knowledge_base_list(api):
    _seed_kb_article_sync("SAP", "How to unlock a user")
    _create_admin_sync("admin_kb@example.com")
    admin_token = api.post(
        "/auth/login", data={"username": "admin_kb@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.get("/knowledge-base", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    titles = [a["title"] for a in resp.json()]
    assert "How to unlock a user" in titles
    # The list view is titles/metadata only, not full article bodies.
    assert "content" not in resp.json()[0]


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


def test_department_list_reports_default_confidence_threshold(api):
    _department_id_sync("Networking")
    token = _register_and_login(api, "sam@example.com")
    resp = api.get("/departments", headers={"Authorization": f"Bearer {token}"})
    networking = next(d for d in resp.json() if d["name"] == "Networking")
    assert networking["confidence_threshold"] == 0.5


def test_updating_department_threshold_requires_admin(api):
    dept_id = _department_id_sync("SAP")
    token = _register_and_login(api, "tara@example.com")
    resp = api.patch(
        f"/departments/{dept_id}/threshold",
        json={"confidence_threshold": 0.7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_updates_department_threshold(api):
    dept_id = _department_id_sync("Database")
    _create_admin_sync("admin_threshold@example.com")
    admin_token = api.post(
        "/auth/login", data={"username": "admin_threshold@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.patch(
        f"/departments/{dept_id}/threshold",
        json={"confidence_threshold": 0.75},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["confidence_threshold"] == 0.75

    listed = api.get("/departments", headers={"Authorization": f"Bearer {admin_token}"}).json()
    database = next(d for d in listed if d["id"] == dept_id)
    assert database["confidence_threshold"] == 0.75


def test_admin_threshold_must_be_within_zero_one(api):
    dept_id = _department_id_sync("Cloud")
    _create_admin_sync("admin_threshold_range@example.com")
    admin_token = api.post(
        "/auth/login", data={"username": "admin_threshold_range@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = api.patch(
        f"/departments/{dept_id}/threshold",
        json={"confidence_threshold": 1.5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422

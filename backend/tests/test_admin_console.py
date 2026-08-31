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

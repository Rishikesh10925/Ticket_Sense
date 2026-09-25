import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, KnowledgeBase, User

AI_EMBEDDINGS_DIR = Path(__file__).resolve().parents[2] / "ai" / "embeddings"
sys.path.insert(0, str(AI_EMBEDDINGS_DIR))


def _register_and_login(api, email: str) -> str:
    api.post("/auth/register", json={"email": email, "full_name": "Test User", "password": "password123"})
    resp = api.post("/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]


def _seed_department_with_article(name: str) -> str:
    async def _seed():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            dept = await db.scalar(select(Department).where(Department.name == name))
            if dept is None:
                dept = Department(name=name)
                db.add(dept)
                await db.flush()
            db.add(
                KnowledgeBase(
                    department_id=dept.id,
                    title="VPN Client Not Connecting",
                    content="VPN client hangs on connecting and never gets in.",
                )
            )
            await db.commit()
            dept_id = str(dept.id)
        await engine.dispose()
        return dept_id

    return asyncio.run(_seed())


def _embed_kb_articles() -> None:
    async def _embed():
        from sentence_transformers import SentenceTransformer

        from app.database import SessionLocal
        from app.models import Embedding
        from retrieve import MODEL_NAME

        model = SentenceTransformer(MODEL_NAME)
        async with SessionLocal() as db:
            articles = list(await db.scalars(select(KnowledgeBase)))
            for article in articles:
                vector = model.encode(article.content, normalize_embeddings=True).tolist()
                db.add(
                    Embedding(
                        knowledge_base_id=article.id,
                        chunk_index=0,
                        chunk_text=article.content,
                        embedding=vector,
                    )
                )
            await db.commit()

    asyncio.run(_embed())


def _admin_token(api, email: str) -> str:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(User(email=email, full_name="Admin", role="admin", hashed_password=hash_password("password123")))
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())
    return api.post("/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]


def _make_engineer_sync(email: str, department_id: str) -> None:
    async def _create():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            db.add(
                User(
                    email=email,
                    full_name="Engineer",
                    role="department_engineer",
                    department_id=department_id,
                    hashed_password=hash_password("password123"),
                )
            )
            await db.commit()
        await engine.dispose()

    asyncio.run(_create())


def test_evidence_empty_before_routing(api):
    # Evidence is reviewer-only (see app/routers/tickets.py's _require_reviewer on
    # this endpoint) — it's the AI's own reasoning material, not something the
    # submitting end_user should see about their own ticket, so this checks the
    # actual "empty before routing" behavior via an admin token instead, and
    # confirms separately that the owning end_user is rejected outright.
    end_user_token = _register_and_login(api, "olga@example.com")
    create_resp = api.post(
        "/tickets",
        data={"subject": "Some issue", "description": "Not yet classified"},
        headers={"Authorization": f"Bearer {end_user_token}"},
    )
    ticket_id = create_resp.json()["id"]

    resp = api.get(f"/tickets/{ticket_id}/evidence", headers={"Authorization": f"Bearer {end_user_token}"})
    assert resp.status_code == 403

    admin_token = _admin_token(api, "olga_admin@example.com")
    resp = api.get(f"/tickets/{ticket_id}/evidence", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_evidence_returns_department_scoped_results(api):
    department_id = _seed_department_with_article("Networking")
    _embed_kb_articles()

    end_user_token = _register_and_login(api, "peter@example.com")
    headers = {"Authorization": f"Bearer {end_user_token}"}
    create_resp = api.post(
        "/tickets",
        data={"subject": "VPN not connecting", "description": "Cannot connect to VPN from home"},
        headers=headers,
    )
    ticket_id = create_resp.json()["id"]

    # Manually route it (no trained classifier artifacts in this test env) to the
    # seeded department, simulating what the Week 4 background task would do.
    async def _route():
        from app.models import Ticket

        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            ticket = await db.get(Ticket, ticket_id)
            ticket.department_id = department_id
            ticket.status = "routed"
            await db.commit()
        await engine.dispose()

    asyncio.run(_route())

    # End user (owner) cannot see the evidence — reviewer-only.
    resp = api.get(f"/tickets/{ticket_id}/evidence", headers=headers)
    assert resp.status_code == 403

    # An engineer in the same department can.
    _make_engineer_sync("engineer_same@example.com", department_id)
    same_dept_token = api.post(
        "/auth/login", data={"username": "engineer_same@example.com", "password": "password123"}
    ).json()["access_token"]
    resp = api.get(
        f"/tickets/{ticket_id}/evidence", headers={"Authorization": f"Bearer {same_dept_token}"}
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["title"] == "VPN Client Not Connecting"

    # An engineer in a different department cannot.
    _make_engineer_sync("engineer_other@example.com", _seed_department_with_article_only_dept())
    other_token = api.post(
        "/auth/login", data={"username": "engineer_other@example.com", "password": "password123"}
    ).json()["access_token"]
    resp = api.get(
        f"/tickets/{ticket_id}/evidence", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert resp.status_code == 403


def _seed_department_with_article_only_dept() -> str:
    async def _seed():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            dept = Department(name="HR")
            db.add(dept)
            await db.commit()
            dept_id = str(dept.id)
        await engine.dispose()
        return dept_id

    return asyncio.run(_seed())

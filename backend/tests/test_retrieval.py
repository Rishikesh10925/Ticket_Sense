import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Department, KnowledgeBase

AI_EMBEDDINGS_DIR = Path(__file__).resolve().parents[2] / "ai" / "embeddings"
sys.path.insert(0, str(AI_EMBEDDINGS_DIR))

from retrieve import retrieve_evidence  # noqa: E402


def _seed_departments_and_articles() -> dict[str, str]:
    """Two departments, one KB article each — enough to prove department scoping
    without needing the real sentence-transformers model to distinguish 60 articles."""

    async def _seed():
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            networking = Department(name="Networking")
            hr = Department(name="HR")
            db.add_all([networking, hr])
            await db.flush()

            db.add(
                KnowledgeBase(
                    department_id=networking.id,
                    title="VPN Client Not Connecting",
                    content="VPN client hangs on connecting and never gets in.",
                )
            )
            db.add(
                KnowledgeBase(
                    department_id=hr.id,
                    title="How to Apply for Leave",
                    content="Steps to submit a leave request in the HR portal.",
                )
            )
            await db.commit()
            ids = {"networking": str(networking.id), "hr": str(hr.id)}
        await engine.dispose()
        return ids

    return asyncio.run(_seed())


def _embed_articles() -> None:
    async def _embed():
        import importlib

        embed_kb = importlib.import_module("embed_knowledge_base")
        # embed_knowledge_base.main() reads from db/seed/knowledge_base/ on disk, which
        # doesn't match this test's ad-hoc articles — call the model + insert directly
        # instead of reusing main().
        from sentence_transformers import SentenceTransformer

        from app.database import SessionLocal
        from app.models import Embedding

        model = SentenceTransformer(embed_kb.MODEL_NAME)
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
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
        await engine.dispose()

    asyncio.run(_embed())


def test_retrieval_is_department_scoped(api):
    # `api` fixture (conftest.py) truncates tables before/after — safe to seed directly.
    department_ids = _seed_departments_and_articles()
    _embed_articles()

    async def _query(department_id: str):
        engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            results = await retrieve_evidence(db, "VPN not connecting from home", department_id, k=3)
        await engine.dispose()
        return results

    networking_results = asyncio.run(_query(department_ids["networking"]))
    assert len(networking_results) == 1
    assert networking_results[0].title == "VPN Client Not Connecting"

    # retrieve_evidence has no relevance threshold — it always returns the department's
    # top-k, however poor the match. The real assertion is that HR-scoped retrieval
    # only ever sees the HR article, never leaks the Networking one, even though the
    # Networking article is the far better semantic match for this query.
    hr_results = asyncio.run(_query(department_ids["hr"]))
    assert len(hr_results) == 1
    assert hr_results[0].title == "How to Apply for Leave"

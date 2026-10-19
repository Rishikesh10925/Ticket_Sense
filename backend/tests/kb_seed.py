"""A knowledge-base article per test department, chunked and embedded like the real
ingest, so the pipeline has evidence to cite. Without evidence a draft cannot answer
and the ticket escalates (Blueprint V2 §9.1), so any test that expects a ticket to
reach `drafted` needs one of these."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Department, KBChunk, KnowledgeBase
from app.routers.knowledge_base import _get_model

ARTICLES = {
    "Networking": (
        "VPN client hangs while connecting",
        "## Symptom\nThe VPN client hangs on connecting from home and never gets in.\n\n"
        "## Resolution steps\n1. Restart the VPN client and sign in again with your network account.\n"
        "2. Check that your home internet connection works without the VPN.\n"
        "3. If it still hangs, reinstall the VPN client from the software portal.\n",
    ),
}
_GENERIC = (
    "General troubleshooting",
    "## Resolution steps\n1. Sign out, close the application and sign in again.\n"
    "2. Restart your computer and try once more.\n",
)


def ensure_article(department_name: str) -> None:
    async def _seed():
        from embeddings.chunking import chunk_markdown

        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            dept = await db.scalar(select(Department).where(Department.name == department_name))
            existing = await db.scalar(select(KnowledgeBase).where(KnowledgeBase.department_id == dept.id))
            if existing is None:
                title, content = ARTICLES.get(department_name, _GENERIC)
                article = KnowledgeBase(department_id=dept.id, title=title, content=content)
                db.add(article)
                await db.flush()
                chunks = chunk_markdown(title, None, content)
                vectors = _get_model().encode([c.text for c in chunks], normalize_embeddings=True)
                for chunk, vector in zip(chunks, vectors):
                    db.add(
                        KBChunk(
                            knowledge_base_id=article.id,
                            chunk_index=chunk.index,
                            sections=",".join(chunk.sections),
                            text=chunk.text,
                            n_tokens=chunk.n_tokens,
                            embedding=vector.tolist(),
                        )
                    )
                await db.commit()
        await engine.dispose()

    asyncio.run(_seed())

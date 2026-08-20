import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.main import app


async def _truncate() -> None:
    # A short-lived engine, created and disposed within this single asyncio.run()
    # call, rather than reusing app.database.engine — that global is bound to
    # whichever event loop first uses it, and TestClient runs the app in its own
    # loop, so sharing one engine across both breaks the connection on Windows.
    truncate_engine = create_async_engine(settings.database_url)
    async with truncate_engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE feedback, escalations, embeddings, tickets, "
                "knowledge_base, users, departments RESTART IDENTITY CASCADE"
            )
        )
    await truncate_engine.dispose()


@pytest.fixture(autouse=True)
def _clean_db():
    """Truncate app tables before/after each test so tests stay isolated from each
    other and from any data a developer has in their local dev database."""
    asyncio.run(_truncate())
    yield
    asyncio.run(_truncate())


@pytest.fixture
def api():
    # Used as a context manager (not just TestClient(app)) so every request in a
    # test shares one anyio portal/event loop — otherwise each request gets its own
    # loop and the app's pooled async engine breaks when reused across loops.
    with TestClient(app) as c:
        yield c

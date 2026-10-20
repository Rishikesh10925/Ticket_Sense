import asyncio
import os
from pathlib import Path

# Tests truncate every app table, so they must never run against the dev database.
# Point the app at a dedicated test database *before* app.config is imported (env vars
# take precedence over .env in pydantic-settings). CI sets TEST_DATABASE_URL itself.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://ticketsense:ticketsense@localhost:5432/ticketsense_test",
)

# No model server or NLI download in tests: offline extractive drafts, lexical claim check.
os.environ["LLM_CLIENT"] = "stub"
os.environ["GROUNDING_SCORER"] = "lexical"

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import make_url, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


async def _ensure_test_database() -> None:
    url = make_url(settings.database_url)
    conn = await asyncpg.connect(
        user=url.username, password=url.password, host=url.host, port=url.port or 5432, database="postgres"
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def _migrated_test_database():
    asyncio.run(_ensure_test_database())
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    yield


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
                "knowledge_base, users, departments, gate_thresholds RESTART IDENTITY CASCADE"
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

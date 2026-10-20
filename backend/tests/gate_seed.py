"""Activate a gate threshold set in the test database. Since Week 9 the gate's lane routes
tickets, and with no active set every draft escalates (the safe default), so tests that
expect a shown draft start from a permissive set (conftest) and tests about the gate set
their own."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import GateThresholds


def set_thresholds(fast: float | None, assisted: float | None, version: str = "test", guard: dict | None = None) -> None:
    async def _go():
        engine = create_async_engine(settings.database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            await db.execute(text("UPDATE gate_thresholds SET active = false"))
            await db.execute(text("DELETE FROM gate_thresholds WHERE version = :v"), {"v": version})
            db.add(GateThresholds(version=version, model_version="confidence-v1-judge", label_source="judge",
                                  alpha_fast=0.1, alpha_assisted=0.4, delta=0.1, fast_threshold=fast,
                                  assisted_threshold=assisted, calibration={"guard": guard or {}}, active=True))
            await db.commit()
        await engine.dispose()

    asyncio.run(_go())

"""Model health counts only tickets the current gate scored and real engineer feedback
(Week 11 bug bash): V1-scored tickets and the V1 synthetic bootstrap are left out."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Feedback, Ticket, User

PASSWORD = "password123"


async def _seed() -> str:
    engine = create_async_engine(settings.database_url)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        s = uuid.uuid4().hex[:6]
        admin = User(email=f"admin.{s}@example.com", full_name="Admin", role="admin", hashed_password=hash_password(PASSWORD))
        engineer = User(email=f"eng.{s}@example.com", full_name="Eng", role="department_engineer",
                        hashed_password=hash_password(PASSWORD))
        synthetic = await db.scalar(select(User).where(User.email == "synthetic-reviewer@ticketsense.local"))
        if synthetic is None:
            synthetic = User(email="synthetic-reviewer@ticketsense.local", full_name="Synthetic", role="admin",
                             hashed_password=hash_password(PASSWORD))
        customer = User(email=f"cust.{s}@example.com", full_name="Cust", role="end_user",
                        hashed_password=hash_password(PASSWORD))
        db.add_all([admin, engineer, synthetic, customer])
        await db.flush()

        def ticket(lane):
            return Ticket(submitted_by=customer.id, subject="VPN", description="VPN down", status="closed",
                          lane=lane, ai_draft_reply="1. Reconnect.", confidence_score=0.8)

        gate, v1, synth = ticket("assisted"), ticket(None), ticket("assisted")
        db.add_all([gate, v1, synth])
        await db.flush()
        db.add_all([
            Feedback(ticket_id=gate.id, reviewer_id=engineer.id, action="accept"),  # counted
            Feedback(ticket_id=v1.id, reviewer_id=engineer.id, action="accept"),  # V1-scored: no lane
            Feedback(ticket_id=synth.id, reviewer_id=synthetic.id, action="reject"),  # synthetic bootstrap
        ])
        await db.commit()
    await engine.dispose()
    return admin.email


def test_model_health_counts_gate_scored_real_feedback_only(api):
    email = asyncio.run(_seed())
    token = api.post("/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    report = api.get("/analytics/confidence-model", headers={"Authorization": f"Bearer {token}"}).json()
    assert report["synthetic_labeled"] == 0
    assert report["total_labeled"] == report["real_labeled"] >= 1
    assert report["overall_agreement_rate"] == 1.0  # the synthetic reject is not counted

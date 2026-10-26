"""No ticket is left stranded by the background pipeline (Week 12): a crash or an
unknown department escalates it to an admin, and approving such an escalation routes it."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models import Department, Escalation, Ticket, User
from app.services import pipeline as pipeline_service
from app.services.ticket_lifecycle import TicketStatus, can_transition

PASSWORD = "password123"


def _session():
    return async_sessionmaker(create_async_engine(settings.database_url), expire_on_commit=False)


async def _ticket() -> uuid.UUID:
    async with _session()() as db:
        s = uuid.uuid4().hex[:6]
        user = User(email=f"cust.{s}@example.com", full_name="Cust", role="end_user",
                    hashed_password=hash_password(PASSWORD))
        db.add(user)
        await db.flush()
        ticket = Ticket(submitted_by=user.id, subject="Printer jam", description="The printer jams.")
        db.add(ticket)
        await db.commit()
        return ticket.id


async def _state(ticket_id):
    async with _session()() as db:
        ticket = await db.get(Ticket, ticket_id)
        escalations = list(await db.scalars(select(Escalation).where(Escalation.ticket_id == ticket_id)))
        return ticket, escalations


class _Pipeline:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    async def ainvoke(self, _state):
        if self.error:
            raise self.error
        return self.result


def test_early_escalation_transitions_are_allowed():
    assert can_transition(TicketStatus.SUBMITTED, TicketStatus.ESCALATED)
    assert can_transition(TicketStatus.CLASSIFIED, TicketStatus.ESCALATED)
    assert not can_transition(TicketStatus.SUBMITTED, TicketStatus.ROUTED)  # stages still cannot be skipped


def test_a_crash_escalates_the_ticket_to_an_admin(monkeypatch):
    ticket_id = asyncio.run(_ticket())
    monkeypatch.setattr(pipeline_service, "build_pipeline",
                        lambda *a, **k: _Pipeline(error=RuntimeError("model server down: Printer jam")))
    asyncio.run(pipeline_service.run_ticket_pipeline(ticket_id))
    ticket, escalations = asyncio.run(_state(ticket_id))
    assert ticket.status == "escalated" and ticket.lane == "escalate"
    assert len(escalations) == 1 and escalations[0].tier == "admin"
    assert "RuntimeError" in escalations[0].reason
    assert "Printer jam" not in escalations[0].reason  # the error message could quote ticket text


def test_an_unknown_department_escalates_instead_of_stalling(monkeypatch):
    ticket_id = asyncio.run(_ticket())
    result = {"department_id": None, "department_name": "Legal", "priority": "low", "sentiment": "neutral",
              "redaction_map": {}}
    monkeypatch.setattr(pipeline_service, "build_pipeline", lambda *a, **k: _Pipeline(result=result))
    asyncio.run(pipeline_service.run_ticket_pipeline(ticket_id))
    ticket, escalations = asyncio.run(_state(ticket_id))
    assert ticket.status == "escalated" and ticket.lane == "escalate" and ticket.department_id is None
    assert len(escalations) == 1 and escalations[0].tier == "admin" and "Legal" in escalations[0].reason


def test_approving_an_unrouted_escalation_routes_the_ticket(api, monkeypatch):
    ticket_id = asyncio.run(_ticket())
    monkeypatch.setattr(pipeline_service, "build_pipeline", lambda *a, **k: _Pipeline(error=ValueError("x")))
    asyncio.run(pipeline_service.run_ticket_pipeline(ticket_id))

    async def people():
        async with _session()() as db:
            s = uuid.uuid4().hex[:6]
            dept = Department(name=f"Facilities-{s}")
            db.add(dept)
            await db.flush()
            admin = User(email=f"admin.{s}@example.com", full_name="Admin", role="admin",
                         hashed_password=hash_password(PASSWORD))
            eng = User(email=f"eng.{s}@example.com", full_name="Eng", role="department_engineer",
                       department_id=dept.id, hashed_password=hash_password(PASSWORD))
            db.add_all([admin, eng])
            await db.flush()
            escalation = await db.scalar(select(Escalation).where(Escalation.ticket_id == ticket_id))
            await db.commit()
            return admin.email, eng.id, escalation.id, dept.id

    admin_email, engineer_id, escalation_id, dept_id = asyncio.run(people())
    token = api.post("/auth/login", data={"username": admin_email, "password": PASSWORD}).json()["access_token"]
    resp = api.post(f"/escalations/{escalation_id}/approve", json={"engineer_id": str(engineer_id)},
                    headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    ticket, _ = asyncio.run(_state(ticket_id))
    assert ticket.department_id == dept_id

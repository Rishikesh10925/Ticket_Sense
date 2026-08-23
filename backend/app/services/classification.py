"""Classify a ticket and route it to a department, updating its lifecycle status.

Runs as a FastAPI BackgroundTask right after ticket creation (see
app/routers/tickets.py) — the HTTP response returns immediately with status
`submitted`, and this updates the ticket to `routed` within a couple of seconds,
matching the Week 4 "classified and routed automatically within a few seconds"
requirement without needing a task queue (Celery/Redis are explicitly out of scope,
see README.md Scope).
"""

import sys
import uuid
from pathlib import Path

# backend/app/services/classification.py -> repo_root/ai must be importable.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Department, Ticket
from app.services.ticket_lifecycle import TicketStatus, transition

from models.classifier import classify_ticket  # noqa: E402


async def classify_and_route(ticket_id: uuid.UUID) -> None:
    # A background task runs after the request's session (from Depends(get_db)) has
    # already closed, so this opens its own — see app/routers/tickets.py.
    async with SessionLocal() as db:
        ticket = await db.get(Ticket, ticket_id)
        if ticket is None:
            return

        result = classify_ticket(ticket.subject, ticket.description)

        department = await db.scalar(
            select(Department).where(Department.name == result.department)
        )

        ticket.priority = result.priority
        ticket.sentiment = result.sentiment
        ticket.status = transition(TicketStatus(ticket.status), TicketStatus.CLASSIFIED)
        await db.flush()

        if department is not None:
            ticket.department_id = department.id
            ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ROUTED)

        await db.commit()

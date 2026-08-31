"""Runs the full classify -> route -> retrieve -> draft LangGraph pipeline for a
ticket and persists every stage's output, advancing the ticket's lifecycle status
through classified -> routed -> drafted as each stage succeeds.

Runs as a FastAPI BackgroundTask right after ticket creation (see
app/routers/tickets.py) — the HTTP response returns immediately with status
`submitted`. This replaces the Week 4 classify_and_route, which stopped at `routed`;
see docs/langgraph-pipeline.md.
"""

import sys
import uuid
from pathlib import Path

# backend/app/services/pipeline.py -> repo_root/ai must be importable.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from app.config import settings
from app.database import SessionLocal
from app.models import Department, Ticket
from app.services.ticket_lifecycle import TicketStatus, transition

from generation.provider_factory import get_llm_provider  # noqa: E402
from graph.pipeline import build_pipeline  # noqa: E402


async def run_ticket_pipeline(ticket_id: uuid.UUID) -> None:
    # A background task runs after the request's session (from Depends(get_db)) has
    # already closed, so this opens its own — see app/routers/tickets.py.
    async with SessionLocal() as db:
        ticket = await db.get(Ticket, ticket_id)
        if ticket is None:
            return

        llm_provider = get_llm_provider(settings.llm_provider)
        pipeline = build_pipeline(db, Department, llm_provider)

        result = await pipeline.ainvoke(
            {"ticket_id": str(ticket.id), "subject": ticket.subject, "description": ticket.description}
        )

        ticket.priority = result.get("priority")
        ticket.sentiment = result.get("sentiment")
        ticket.status = transition(TicketStatus(ticket.status), TicketStatus.CLASSIFIED)
        await db.flush()

        department_id = result.get("department_id")
        if department_id is not None:
            ticket.department_id = uuid.UUID(department_id)
            ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ROUTED)
            await db.flush()

            # Evidence retrieval (and therefore a grounded draft) only makes sense once
            # a department is known to scope the search to — matches the existing rule
            # in app/services/retrieval.py's get_evidence_for_ticket. Without a
            # department the ticket stays at `routed` and un-drafted.
            ticket.ai_draft_reply = result.get("draft")
            ticket.ai_draft_citations = result.get("citations") or []
            ticket.status = transition(TicketStatus(ticket.status), TicketStatus.DRAFTED)

        await db.commit()

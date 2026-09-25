"""Runs the full extract -> classify -> route -> retrieve -> score -> [confidence
gate] -> draft | escalate LangGraph pipeline for a ticket and persists every stage's
output, advancing the ticket's lifecycle status through classified -> routed ->
drafted | escalated as each stage succeeds.

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
from app.models import Department, Escalation, Ticket
from app.models.department import DEFAULT_CONFIDENCE_THRESHOLD
from app.schemas.tickets import CUSTOMER_READY_CONFIDENCE_THRESHOLD
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
        pipeline = build_pipeline(db, Department, llm_provider, DEFAULT_CONFIDENCE_THRESHOLD)

        result = await pipeline.ainvoke(
            {
                "ticket_id": str(ticket.id),
                "subject": ticket.subject,
                "description": ticket.description,
                "attachment_path": ticket.attachment_path,
                "attachment_type": ticket.attachment_type,
            }
        )

        ticket.attachment_text = result.get("attachment_text")
        ticket.ocr_confidence = result.get("ocr_confidence")

        ticket.priority = result.get("priority")
        ticket.sentiment = result.get("sentiment")
        ticket.status = transition(TicketStatus(ticket.status), TicketStatus.CLASSIFIED)
        await db.flush()

        department_id = result.get("department_id")
        if department_id is not None:
            ticket.department_id = uuid.UUID(department_id)
            ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ROUTED)
            await db.flush()

            # Confidence scoring now runs before drafting (Week 9's gate — see
            # ai/graph/pipeline.py) — persisted regardless of which branch the gate
            # took, since a score/threshold exist either way. score/threshold/features
            # are the full log of "what the gate saw" — see docs/langgraph-pipeline.md
            # for why no separate decision-log table was added.
            ticket.confidence_score = result.get("confidence_score")
            ticket.confidence_features = result.get("confidence_features")
            ticket.confidence_threshold = result.get("confidence_threshold")

            if result.get("gate_decision") == "draft":
                ticket.ai_draft_reply = result.get("draft")
                ticket.ai_draft_citations = result.get("citations") or []
                ticket.status = transition(TicketStatus(ticket.status), TicketStatus.DRAFTED)

                # Auto-resolution: a draft that clears the (separate, higher)
                # customer-facing bar goes straight to the customer, no engineer ever
                # sees it — no Feedback row is created, since no one reviewed it; see
                # app/routers/tickets.py's _final_responses_for, which treats a
                # `reviewed` ticket with zero Feedback rows as exactly this case.
                if ticket.confidence_score >= CUSTOMER_READY_CONFIDENCE_THRESHOLD:
                    ticket.status = transition(TicketStatus(ticket.status), TicketStatus.REVIEWED)
            else:
                # Gate failed: no draft is generated or shown (docs/architecture.md's
                # "Example" — "escalated ... with the draft withheld") — the ticket
                # goes straight to a human, and the Escalation row records why.
                ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ESCALATED)
                db.add(
                    Escalation(
                        ticket_id=ticket.id,
                        reason=(
                            f"Confidence score {ticket.confidence_score:.3f} below "
                            f"department threshold {ticket.confidence_threshold:.3f}"
                        ),
                        confidence_score=ticket.confidence_score,
                    )
                )

        await db.commit()

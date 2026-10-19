"""Runs the full ticket pipeline (extract -> classify -> route -> retrieve -> draft ->
check -> score -> [gate] -> show | escalate) and persists every stage's output,
advancing the ticket's lifecycle status through classified -> routed -> drafted |
escalated as each stage succeeds.

Runs as a FastAPI BackgroundTask right after ticket creation (see
app/routers/tickets.py) — the HTTP response returns immediately with status
`submitted`. See docs/langgraph-pipeline.md.

Every structured draft is stored in `drafts`, with its claims and support scores in
`draft_claims`, whichever way the gate went. Only a shown draft is copied onto the
ticket (`ai_draft_reply`, `ai_draft_citations`) where the engineer sees it.
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
from app.models.draft import Draft, DraftClaim
from app.services.ticket_lifecycle import TicketStatus, transition

from generation.llm import get_llm_client  # noqa: E402
from graph.nodes import get_scorer  # noqa: E402
from graph.pipeline import build_pipeline  # noqa: E402


def _draft_row(ticket_id: uuid.UUID, result: dict) -> Draft | None:
    draft = result.get("draft_result")
    if not draft or "raw_text" not in draft:
        return None  # the model was unreachable; nothing was generated
    grounding = result.get("grounding") or {}
    run_id = result.get("retrieval_run_id")
    row = Draft(
        ticket_id=ticket_id,
        retrieval_run_id=uuid.UUID(run_id) if run_id else None,
        model=draft["model"],
        prompt_version=draft["prompt_version"],
        schema_valid=draft["schema_valid"],
        can_answer=draft["can_answer"],
        steps=draft["steps"],
        missing_information=draft["missing_information"],
        evidence=[
            {k: p[k] for k in ("n", "article_key", "title", "text")} for p in result.get("passages") or []
        ],
        raw_text=draft["raw_text"],
        groundedness=grounding.get("groundedness"),
    )
    row.claims = [
        DraftClaim(
            step_index=c["step_index"],
            claim_index=c["claim_index"],
            text=c["text"],
            cited=c["cited"],
            support=c["support"],
        )
        for c in grounding.get("claims") or []
    ]
    return row


def _escalation_reason(ticket: Ticket, result: dict) -> str:
    draft = result.get("draft_result") or {}
    if draft.get("rejection"):
        return f"Draft rejected: {draft['rejection']}"
    if draft and draft.get("can_answer") is False:
        return "The evidence does not answer this ticket"
    return (
        f"Confidence score {ticket.confidence_score:.3f} below "
        f"department threshold {ticket.confidence_threshold:.3f}"
    )


async def run_ticket_pipeline(ticket_id: uuid.UUID) -> None:
    # A background task runs after the request's session (from Depends(get_db)) has
    # already closed, so this opens its own — see app/routers/tickets.py.
    async with SessionLocal() as db:
        ticket = await db.get(Ticket, ticket_id)
        if ticket is None:
            return

        pipeline = build_pipeline(
            db,
            Department,
            get_llm_client(settings.llm_client),
            scorer=get_scorer(settings.grounding_scorer),
            default_confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
        )

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

            draft_row = _draft_row(ticket.id, result)
            if draft_row is not None:
                db.add(draft_row)

            # score/threshold/features are the full log of "what the gate saw" — see
            # docs/langgraph-pipeline.md for why no separate decision-log table was added.
            ticket.confidence_score = result.get("confidence_score")
            ticket.confidence_features = result.get("confidence_features")
            ticket.confidence_threshold = result.get("confidence_threshold")

            if result.get("gate_decision") == "draft":
                ticket.ai_draft_reply = result.get("draft")
                ticket.ai_draft_citations = result.get("citations") or []
                ticket.status = transition(TicketStatus(ticket.status), TicketStatus.DRAFTED)

                # No auto-resolution: a drafted ticket always waits for a human
                # decision (Blueprint V2 §7 — the human always makes the final call).
            else:
                # Escalation lane: no AI draft is shown (Blueprint V2 §9.1). The draft
                # stays in `drafts` for evaluation; the Escalation row records why.
                ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ESCALATED)
                db.add(
                    Escalation(
                        ticket_id=ticket.id,
                        reason=_escalation_reason(ticket, result),
                        confidence_score=ticket.confidence_score,
                    )
                )

        await db.commit()

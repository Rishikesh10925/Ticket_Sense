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
from app.models.draft import Draft, DraftClaim, SignalVector
from app.models.gate import GateDecision
from app.services.ticket_lifecycle import TicketStatus, transition

from generation.llm import get_llm_client  # noqa: E402
from security.pii import REDACTOR_VERSION, restore  # noqa: E402
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
    gate = result.get("gate_v2") or {}
    if gate.get("thresholds_id") is None:
        return "No certified thresholds are active, so every draft escalates"
    reasons = gate.get("reasons") or []
    if reasons and reasons[0].startswith(("uncertain routing", "another department")):
        return f"Shift guard: {reasons[0]}"
    score = "unknown" if ticket.confidence_score is None else f"{ticket.confidence_score:.3f}"
    threshold = gate.get("assisted_threshold")
    shown = "not certified" if threshold is None else f"{threshold:.3f}"
    return (f"Confidence score {score} below the assisted-lane threshold {shown} "
            f"(thresholds {gate.get('thresholds_version')})")


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
        ticket.redacted_text = "\n\n".join(
            part
            for part in (
                result.get("redacted_subject"),
                result.get("redacted_description"),
                result.get("redacted_attachment"),
            )
            if part
        )
        redaction_map = result.get("redaction_map") or {}
        ticket.redaction_map = redaction_map
        ticket.redactor_version = REDACTOR_VERSION
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
                signals = result.get("signals")
                gate = result.get("gate_v2")
                if gate:
                    await db.flush()
                    db.add(
                        GateDecision(
                            draft_id=draft_row.id,
                            thresholds_id=uuid.UUID(gate["thresholds_id"]) if gate["thresholds_id"] else None,
                            model_version=gate["model_version"],
                            score=gate["score"],
                            lane=gate["lane"],
                            reasons=gate["reasons"],
                        )
                    )
                if signals:
                    await db.flush()
                    db.add(
                        SignalVector(
                            draft_id=draft_row.id, feature_version=signals["feature_version"], features=signals
                        )
                    )

            # The gate's decision is logged in gate_decisions; the ticket keeps the lane,
            # the calibrated score and the assisted-lane threshold it was compared with.
            gate = result.get("gate_v2") or {}
            ticket.lane = gate.get("lane") or "escalate"
            ticket.confidence_score = gate.get("score")
            ticket.confidence_threshold = gate.get("assisted_threshold")
            ticket.confidence_features = None  # V1 feature bars; V2 reasons live in gate_decisions

            if result.get("gate_decision") == "draft":
                # The model only saw placeholders; the engineer's copy gets the real
                # values back. The stored draft row keeps the placeholders.
                ticket.ai_draft_reply = restore(result.get("draft") or "", redaction_map) or None
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
                        tier="senior",  # the gate withheld the draft: senior queue (Blueprint V2 §9.1)
                    )
                )

        await db.commit()

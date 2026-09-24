from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# A second, customer-facing threshold — separate from a department's own gate
# threshold (Department.confidence_threshold, which only decides draft vs. escalate
# in the LangGraph pipeline). This one decides what an end_user sees for a ticket
# that already cleared the gate and reached `drafted`: above it, they're told a
# resolution is ready and awaiting an engineer's final approval; at or below it,
# they see the same "being reviewed" message as always. It never changes whether a
# human reviews the ticket — see build_ticket_out and docs/architecture.md.
CUSTOMER_READY_CONFIDENCE_THRESHOLD = 0.85


class TicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class TicketOut(BaseModel):
    id: UUID
    submitted_by: UUID
    department_id: UUID | None
    subject: str
    description: str
    attachment_path: str | None
    attachment_type: str | None
    attachment_text: str | None
    ocr_confidence: float | None
    priority: str | None
    sentiment: str | None
    status: str
    ai_draft_reply: str | None
    ai_draft_citations: list[dict] | None
    confidence_score: float | None
    confidence_features: dict | None
    confidence_threshold: float | None
    # Computed in build_ticket_out, not a real column — see
    # CUSTOMER_READY_CONFIDENCE_THRESHOLD above. Visible to every role: it reveals
    # nothing about the actual score, only whether a human still needs to approve
    # before this reaches the end user, which is exactly what the end_user's own UI
    # needs to know without seeing the score itself.
    high_confidence_ready: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def build_ticket_out(ticket, role: str) -> TicketOut:
    """TicketSense does not send AI-generated drafts to end users directly — a human
    engineer always makes the final call (see docs/architecture.md) — so the draft, its
    citations, and the confidence score/features/threshold that judge it are stripped
    for the end_user role here rather than in the ORM layer, which keeps the underlying
    ticket record itself untouched. attachment_text/ocr_confidence are NOT stripped —
    that's text extracted straight from the submitter's own attachment, not an AI
    judgment about it, so every role that can see the ticket can see it."""
    out = TicketOut.model_validate(ticket)
    update: dict = {
        "high_confidence_ready": (
            ticket.status == "drafted"
            and ticket.confidence_score is not None
            and ticket.confidence_score >= CUSTOMER_READY_CONFIDENCE_THRESHOLD
        )
    }
    if role == "end_user":
        update.update(
            {
                "ai_draft_reply": None,
                "ai_draft_citations": None,
                "confidence_score": None,
                "confidence_features": None,
                "confidence_threshold": None,
            }
        )
    return out.model_copy(update=update)

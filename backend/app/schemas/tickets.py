from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# The auto-resolution bar: a `drafted` ticket whose score clears this is sent straight
# to the customer with no human ever reviewing it (see app/services/pipeline.py) —
# deliberately separate from a department's own gate threshold
# (Department.confidence_threshold, which only decides draft vs. escalate). Below the
# gate threshold, a ticket never even gets a draft; between the gate threshold and this
# one, a real engineer reviews it (see docs/architecture.md for why that band still
# gets a human); at or above this one, nothing does.
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
    # Computed by the caller (see _final_responses_for in app/routers/tickets.py), not
    # a real column — the actual text that was (or, for an auto-resolution, would be)
    # sent to the customer once status is `reviewed`. Unlike ai_draft_reply, this is
    # deliberately visible to every role including end_user: it's the one AI-touched
    # piece of text a customer is *meant* to see, since a human either wrote/approved
    # it (an engineer's accept/edit/resolve) or the ticket cleared the auto-resolution
    # bar outright.
    final_response: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def build_ticket_out(ticket, role: str, final_response: str | None = None) -> TicketOut:
    """TicketSense does not send AI-generated drafts to end users directly while a
    ticket is still awaiting a decision — a human engineer always makes the final call
    on anything in the `drafted`/`escalated` band (see docs/architecture.md) — so the
    draft, its citations, and the confidence score/features/threshold that judge it are
    stripped for the end_user role here rather than in the ORM layer, which keeps the
    underlying ticket record itself untouched. attachment_text/ocr_confidence are NOT
    stripped — that's text extracted straight from the submitter's own attachment, not
    an AI judgment about it, so every role that can see the ticket can see it.
    `final_response` is never stripped for any role — see TicketOut's own docstring."""
    out = TicketOut.model_validate(ticket)
    update: dict = {"final_response": final_response}
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

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    if role == "end_user":
        out = out.model_copy(
            update={
                "ai_draft_reply": None,
                "ai_draft_citations": None,
                "confidence_score": None,
                "confidence_features": None,
                "confidence_threshold": None,
            }
        )
    return out

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.reason_codes import ReasonCode


class FeedbackCreate(BaseModel):
    # 'doubt' (drafted only): the engineer isn't sure how to handle this ticket and
    # sends it back to the admin approval queue instead of deciding — reuses
    # reject_reason as its note field, matching the same "required non-empty text"
    # validation reject already gets. 'resolve' isn't submitted here — it's the
    # engineer response body for POST /tickets/{id}/resolve-escalation instead.
    action: Literal["accept", "edit", "reject", "escalate", "doubt"]
    edited_reply: str | None = None
    reject_reason: str | None = None
    # Workbench (Week 7): optional for V1 clients, always sent by the workbench.
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    time_taken_ms: int | None = Field(default=None, ge=0, le=3_600_000)


class FeedbackOut(BaseModel):
    id: UUID
    ticket_id: UUID
    reviewer_id: UUID
    action: str
    edited_reply: str | None
    reject_reason: str | None
    reason_codes: list[str]
    time_taken_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

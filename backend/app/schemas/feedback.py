from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    # 'doubt' (drafted only): the engineer isn't sure how to handle this ticket and
    # sends it back to the admin approval queue instead of deciding — reuses
    # reject_reason as its note field, matching the same "required non-empty text"
    # validation reject already gets. 'resolve' isn't submitted here — it's the
    # engineer response body for POST /tickets/{id}/resolve-escalation instead.
    action: Literal["accept", "edit", "reject", "escalate", "doubt"]
    edited_reply: str | None = None
    reject_reason: str | None = None


class FeedbackOut(BaseModel):
    id: UUID
    ticket_id: UUID
    reviewer_id: UUID
    action: str
    edited_reply: str | None
    reject_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

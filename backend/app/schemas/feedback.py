from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    action: Literal["accept", "edit", "reject", "escalate"]
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

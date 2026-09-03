from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EscalationOut(BaseModel):
    id: UUID
    ticket_id: UUID
    reason: str
    confidence_score: float | None
    escalated_to: UUID | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

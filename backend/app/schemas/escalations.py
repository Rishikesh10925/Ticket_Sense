from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EscalationOut(BaseModel):
    id: UUID
    ticket_id: UUID
    reason: str
    confidence_score: float | None
    escalated_to: UUID | None
    admin_decision: str | None
    admin_note: str | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingEscalationOut(BaseModel):
    """One row in the admin approval queue — the escalation plus enough of its
    ticket's own context (subject, department, priority) that admin doesn't need a
    second request per row just to render the list."""

    id: UUID
    ticket_id: UUID
    ticket_subject: str
    department_id: UUID | None
    department_name: str | None
    priority: str | None
    reason: str
    confidence_score: float | None
    created_at: datetime


class EscalationApprove(BaseModel):
    engineer_id: UUID


class EscalationReject(BaseModel):
    note: str


class EscalationResolve(BaseModel):
    response_text: str

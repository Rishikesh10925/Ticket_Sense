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
    priority: str | None
    sentiment: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

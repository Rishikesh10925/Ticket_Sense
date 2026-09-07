from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseOut(BaseModel):
    id: UUID
    department_id: UUID
    title: str
    source_url: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    department_id: UUID
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_url: str | None = None

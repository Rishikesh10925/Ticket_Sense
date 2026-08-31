from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeBaseOut(BaseModel):
    id: UUID
    department_id: UUID
    title: str
    source_url: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}

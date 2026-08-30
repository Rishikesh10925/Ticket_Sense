from uuid import UUID

from pydantic import BaseModel


class EvidenceOut(BaseModel):
    source_type: str  # "knowledge_base" | "resolved_ticket"
    source_id: UUID
    title: str
    snippet: str
    distance: float

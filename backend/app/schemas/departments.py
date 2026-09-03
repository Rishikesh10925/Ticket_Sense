from uuid import UUID

from pydantic import BaseModel, Field


class DepartmentOut(BaseModel):
    id: UUID
    name: str
    confidence_threshold: float

    model_config = {"from_attributes": True}


class DepartmentThresholdUpdate(BaseModel):
    confidence_threshold: float = Field(ge=0.0, le=1.0)

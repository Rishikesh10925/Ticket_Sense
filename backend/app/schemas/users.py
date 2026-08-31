from uuid import UUID

from pydantic import BaseModel


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    department_id: UUID | None

    model_config = {"from_attributes": True}

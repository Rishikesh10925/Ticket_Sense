from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    department_id: UUID | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Admin-only account creation for the two roles that can't self-register via
    POST /auth/register (see app/routers/auth.py) — department_engineer and admin.
    Before this existed, the only way to onboard a new engineer was the
    seed_demo_users.py script, which isn't something an admin can run in production."""

    email: str
    full_name: str
    password: str
    role: Literal["end_user", "department_engineer", "admin"]
    department_id: UUID | None = None


class UserUpdate(BaseModel):
    """Partial update — role/department reassignment and activate/deactivate.
    All fields optional; only the ones provided are changed."""

    role: Literal["end_user", "department_engineer", "admin"] | None = None
    department_id: UUID | None = None
    is_active: bool | None = None

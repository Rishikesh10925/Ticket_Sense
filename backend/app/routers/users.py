import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import get_db
from app.dependencies import require_role
from app.models import User
from app.schemas.users import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    result = await db.scalars(select(User).order_by(User.role, User.full_name))
    return list(result)


@router.post("", response_model=UserOut, status_code=http_status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admin-provisioned account creation — the only way to onboard a
    department_engineer or admin (see app/routers/auth.py::register, which is
    deliberately end_user-only). Previously this required the seed_demo_users.py
    script; this closes that gap for the Week 10 admin user-management screen."""
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        department_id=body.department_id,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Role/department reassignment and activate/deactivate. `is_active=False`
    doesn't delete anything — it just makes get_current_user reject that user's
    token on their next request (see app/dependencies.py), so their existing
    tickets/feedback stay intact."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

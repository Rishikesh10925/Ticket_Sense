from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import User
from app.schemas.users import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    result = await db.scalars(select(User).order_by(User.role, User.full_name))
    return list(result)

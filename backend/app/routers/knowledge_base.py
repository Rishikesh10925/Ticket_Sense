from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import KnowledgeBase, User
from app.schemas.knowledge_base import KnowledgeBaseOut

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_knowledge_base(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBase]:
    # Article bodies aren't in KnowledgeBaseOut — this is the admin console's list
    # view (title/department/source), not the article-detail screen that doesn't
    # exist yet.
    result = await db.scalars(select(KnowledgeBase).order_by(KnowledgeBase.department_id, KnowledgeBase.title))
    return list(result)

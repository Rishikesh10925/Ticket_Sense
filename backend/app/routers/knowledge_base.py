import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import Department, Embedding, KnowledgeBase, User
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseOut

# app/routers/knowledge_base.py -> repo_root/ai must be importable, same pattern as
# app/services/retrieval.py — this router is the only backend/ code that needs to
# embed new content rather than just query already-embedded content.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

_model = None  # lazy-loaded singleton, same pattern as ai/embeddings/retrieve.py


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


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


@router.post("", response_model=KnowledgeBaseOut, status_code=http_status.HTTP_201_CREATED)
async def create_knowledge_base_article(
    body: KnowledgeBaseCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    """Admin-authored knowledge-base articles, in addition to the seeded ones from
    db/seed/knowledge_base/ (ai/embeddings/embed_knowledge_base.py). Embeds the new
    article's content immediately using the same model/normalization as that script —
    a KB row with no embedding row would be invisible to retrieve_evidence (Week 5),
    so this can't just insert the row and leave embedding for a later batch job."""
    department = await db.get(Department, body.department_id)
    if department is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Department not found")

    article = KnowledgeBase(
        department_id=body.department_id,
        title=body.title,
        content=body.content,
        source_url=body.source_url,
    )
    db.add(article)
    await db.flush()

    vector = _get_model().encode(body.content, normalize_embeddings=True).tolist()
    db.add(Embedding(knowledge_base_id=article.id, chunk_index=0, chunk_text=body.content, embedding=vector))

    await db.commit()
    await db.refresh(article)
    return article

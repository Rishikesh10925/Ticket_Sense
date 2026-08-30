"""Department-scoped similarity-search retrieval over the knowledge base and resolved
tickets. This is the function backend/app/services/retrieval.py wires into the live
ticket-evidence API endpoint (Week 5, Rishikesh) — see docs/retrieval.md.

Department scoping happens in the SQL WHERE clause (joined to `knowledge_base.
department_id` / `tickets.department_id`), not as a Python-side post-filter — an SAP
query can only ever match rows already restricted to the SAP department at the
database level. See docs/retrieval.md for why this matters (no cross-department
leakage, verified in the Week 5 Team Integration check).
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Embedding, KnowledgeBase, Ticket

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


@dataclass
class EvidenceResult:
    source_type: str  # "knowledge_base" | "resolved_ticket"
    source_id: UUID
    title: str
    snippet: str
    department_id: UUID
    distance: float


async def retrieve_evidence(
    db: AsyncSession, query_text: str, department_id: UUID, k: int = 5
) -> list[EvidenceResult]:
    """Top-k evidence for query_text, scoped to department_id, merged from both
    sources. Fetches top-k from each source separately (each already department-scoped
    at the SQL level) then merges — correct for the combined top-k, since any item in
    the true top-k of the union must be within the top-k of whichever source it's in.
    """
    query_vector = _get_model().encode(query_text, normalize_embeddings=True).tolist()
    distance = Embedding.embedding.cosine_distance(query_vector)

    kb_stmt = (
        select(
            KnowledgeBase.id, KnowledgeBase.title, Embedding.chunk_text, distance.label("distance")
        )
        .join(KnowledgeBase, Embedding.knowledge_base_id == KnowledgeBase.id)
        .where(KnowledgeBase.department_id == department_id)
        .order_by(distance)
        .limit(k)
    )
    ticket_stmt = (
        select(Ticket.id, Ticket.subject, Embedding.chunk_text, distance.label("distance"))
        .join(Ticket, Embedding.ticket_id == Ticket.id)
        .where(Ticket.department_id == department_id)
        .order_by(distance)
        .limit(k)
    )

    kb_rows = (await db.execute(kb_stmt)).all()
    ticket_rows = (await db.execute(ticket_stmt)).all()

    results = [
        EvidenceResult(
            source_type="knowledge_base",
            source_id=row.id,
            title=row.title,
            snippet=row.chunk_text,
            department_id=department_id,
            distance=row.distance,
        )
        for row in kb_rows
    ] + [
        EvidenceResult(
            source_type="resolved_ticket",
            source_id=row.id,
            title=row.subject,
            snippet=row.chunk_text,
            department_id=department_id,
            distance=row.distance,
        )
        for row in ticket_rows
    ]

    results.sort(key=lambda r: r.distance)
    return results[:k]

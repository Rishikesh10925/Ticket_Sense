"""Evidence for a ticket, read back from the retrieval run the pipeline logged
(ai/retrieval/run_log.py, migration 0013), so an engineer sees exactly the passages the
draft and the confidence model used. See app/routers/tickets.py's evidence endpoint.
"""

import sys
from pathlib import Path

# backend/app/services/retrieval.py -> repo_root/ai must be importable.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket

from embeddings.retrieve import EvidenceResult  # noqa: E402
from retrieval.run_log import logged_evidence  # noqa: E402

__all__ = ["EvidenceResult", "get_evidence_for_ticket"]


async def get_evidence_for_ticket(db: AsyncSession, ticket: Ticket, k: int = 5) -> list[EvidenceResult]:
    """Empty until the pipeline has routed the ticket and logged a retrieval run."""
    if ticket.department_id is None:
        return []
    return (await logged_evidence(db, ticket.id))[:k]

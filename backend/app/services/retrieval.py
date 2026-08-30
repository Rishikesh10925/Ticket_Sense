"""Thin wrapper around ai/embeddings/retrieve.py's department-scoped retrieval
function, for the backend to call without needing to know ai/'s import path itself.
See docs/retrieval.md and app/routers/tickets.py's evidence endpoint.
"""

import sys
from pathlib import Path

# backend/app/services/retrieval.py -> repo_root/ai must be importable.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket

from embeddings.retrieve import EvidenceResult, retrieve_evidence  # noqa: E402

__all__ = ["EvidenceResult", "get_evidence_for_ticket"]


async def get_evidence_for_ticket(db: AsyncSession, ticket: Ticket, k: int = 5) -> list[EvidenceResult]:
    """No evidence to retrieve until the ticket has been routed to a department —
    returns an empty list rather than guessing, since there's no department to scope
    the search to yet (see docs/ticket-lifecycle.md)."""
    if ticket.department_id is None:
        return []

    query_text = f"{ticket.subject}\n\n{ticket.description}"
    return await retrieve_evidence(db, query_text, ticket.department_id, k=k)

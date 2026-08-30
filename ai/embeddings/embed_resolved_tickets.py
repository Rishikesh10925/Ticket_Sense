"""Generate embeddings for resolved (closed) tickets, as a second evidence source
alongside the knowledge base (see ai/embeddings/embed_knowledge_base.py and
docs/retrieval.md).

No real resolved-ticket history exists yet, since the review/drafting workflow that
would produce one isn't built until a later week — this embeds whatever tickets
currently have `status = 'closed'`, which right now means the 120 synthetic tickets
from data/seed_synthetic_tickets.py. Written generally (filters on status, not on the
synthetic placeholder account) so it keeps working once real tickets close.

Requires the `ai` extra: `uv sync --extra ai` (from backend/).

Usage (from repo root):
    uv run --project backend --extra ai python ai/embeddings/embed_resolved_tickets.py
"""

import asyncio
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import delete, select

# ai/embeddings/embed_resolved_tickets.py -> repo_root/backend must be importable.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import Embedding, Ticket  # noqa: E402

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


async def main() -> None:
    print(f"loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    async with SessionLocal() as db:
        tickets = list(await db.scalars(select(Ticket).where(Ticket.status == "closed")))
        embedded = 0

        for ticket in tickets:
            content = f"{ticket.subject}\n\n{ticket.description}"

            await db.execute(delete(Embedding).where(Embedding.ticket_id == ticket.id))
            vector = model.encode(content, normalize_embeddings=True).tolist()
            db.add(
                Embedding(ticket_id=ticket.id, chunk_index=0, chunk_text=content, embedding=vector)
            )
            embedded += 1

        await db.commit()

    print(f"embedded {embedded} closed tickets")


if __name__ == "__main__":
    asyncio.run(main())

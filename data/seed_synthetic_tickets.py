"""Insert the synthetic labeled tickets into the `tickets` table as closed historical
tickets, so there's something for ai/embeddings/embed_resolved_tickets.py to embed.

No real resolved-ticket history exists yet — the review/drafting workflow that would
produce one isn't built until a later week (see docs/retrieval.md). Rather than skip
"historical resolved tickets" retrieval entirely, or pretend synthetic data is real,
this inserts the same 120 hand-authored tickets already used for classifier training
(data/synthetic_labeled_tickets.py) as `closed` tickets attributed to a placeholder
account, clearly identifiable and easy to clean out later — the same pattern an earlier
prototype used for the same reason (recovered from git history).

Requires the five departments to already exist (see
backend/app/scripts/seed_demo_users.py) and DATABASE_URL configured (.env).

Usage (from repo root):
    uv run --project backend python data/seed_synthetic_tickets.py [--reset]
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete, select

# data/seed_synthetic_tickets.py -> repo_root/backend must be importable, and
# data/synthetic_labeled_tickets.py (sibling file) must be importable too.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "data"))

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Department, Ticket, User  # noqa: E402

from synthetic_labeled_tickets import TICKETS  # noqa: E402

PLACEHOLDER_EMAIL = "synthetic-tickets@ticketsense.local"


async def main(reset: bool) -> None:
    async with SessionLocal() as db:
        placeholder = await db.scalar(select(User).where(User.email == PLACEHOLDER_EMAIL))
        if placeholder is None:
            placeholder = User(
                email=PLACEHOLDER_EMAIL,
                full_name="Synthetic Ticket Set",
                role="end_user",
                hashed_password=hash_password("not-a-real-account"),
            )
            db.add(placeholder)
            await db.flush()

        existing = await db.scalar(
            select(Ticket).where(Ticket.submitted_by == placeholder.id).limit(1)
        )
        if existing is not None and not reset:
            print("synthetic tickets already seeded, skipping (pass --reset to replace them)")
            return
        if existing is not None:
            await db.execute(delete(Ticket).where(Ticket.submitted_by == placeholder.id))
            print("--reset: removed previously seeded synthetic tickets")

        department_cache: dict[str, Department] = {}
        inserted = 0
        for department_name, subject, description, priority, sentiment in TICKETS:
            if department_name not in department_cache:
                dept = await db.scalar(select(Department).where(Department.name == department_name))
                if dept is None:
                    raise SystemExit(
                        f"Department '{department_name}' not found — seed departments first "
                        "(see backend/app/scripts/seed_demo_users.py)."
                    )
                department_cache[department_name] = dept

            db.add(
                Ticket(
                    submitted_by=placeholder.id,
                    department_id=department_cache[department_name].id,
                    subject=subject,
                    description=description,
                    priority=priority,
                    sentiment=sentiment,
                    status="closed",
                )
            )
            inserted += 1

        await db.commit()
        print(f"inserted {inserted} synthetic historical tickets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.reset))

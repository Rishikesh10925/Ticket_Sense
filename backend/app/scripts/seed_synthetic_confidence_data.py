"""Bootstraps confidence-model training data by scoring the synthetic historical
tickets (data/seed_synthetic_tickets.py) through the real feature pipeline and logging
a synthetic reviewer outcome for each — see docs/confidence-model.md and
docs/confidence-labelling-guide.md.

Every row this writes is clearly synthetic: the reviewer is a placeholder account
(synthetic-reviewer@ticketsense.local), the same pattern already used for the
synthetic ticket submitter (synthetic-tickets@ticketsense.local, see
data/seed_synthetic_tickets.py). This is Rishikesh's half of Week 8's "begin logging
simulated/synthetic review outcomes to bootstrap training data" — Shivaganesh's
ai/confidence/train.py computes the same features offline for model training; this
script persists them onto real ticket rows and logs a real (synthetically-labelled)
`feedback` row for each, so the live schema/logging path this data eventually flows
through is exercised now rather than only at training time.

Idempotent — skips any ticket that already has a synthetic-reviewer feedback row, so
re-running after new synthetic tickets are seeded only scores/logs the new ones.

Usage (from backend/):
    uv run python app/scripts/seed_synthetic_confidence_data.py
Requires the `ai` extra, a migrated database, and the confidence model already trained
(`uv run python ../ai/confidence/train.py` — see ai/README.md).
"""

import asyncio
import random
import sys
from pathlib import Path

AI_DIR = Path(__file__).resolve().parents[3] / "ai"
for _sub in ("embeddings", "confidence"):
    _p = str(AI_DIR / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Department, Feedback, Ticket, User  # noqa: E402
from app.models.department import DEFAULT_CONFIDENCE_THRESHOLD  # noqa: E402

from retrieve import retrieve_evidence  # noqa: E402
from features import compute_features  # noqa: E402
from predict import predict_confidence  # noqa: E402
from synthetic_labels import simulate_outcome  # noqa: E402

SYNTHETIC_REVIEWER_EMAIL = "synthetic-reviewer@ticketsense.local"
SEED = 42
REJECT_REASON = (
    "Synthetic bootstrap label — simulated low confidence, not a real reviewer "
    "judgment. See docs/confidence-model.md."
)


async def _get_or_create_reviewer(db) -> User:
    reviewer = await db.scalar(select(User).where(User.email == SYNTHETIC_REVIEWER_EMAIL))
    if reviewer is None:
        reviewer = User(
            email=SYNTHETIC_REVIEWER_EMAIL,
            full_name="Synthetic Reviewer (bootstrap data)",
            role="department_engineer",
            hashed_password=hash_password("not-a-real-account"),
        )
        db.add(reviewer)
        await db.flush()
    return reviewer


async def main() -> None:
    rng = random.Random(SEED)
    scored = 0
    logged = 0
    skipped_existing = 0

    async with SessionLocal() as db:
        reviewer = await _get_or_create_reviewer(db)
        departments = {d.id: d for d in await db.scalars(select(Department))}
        tickets = list(
            await db.scalars(
                select(Ticket).where(Ticket.status == "closed", Ticket.department_id.is_not(None))
            )
        )

        for ticket in tickets:
            department = departments.get(ticket.department_id)
            department_name = department.name if department else None
            threshold = float(department.confidence_threshold) if department else DEFAULT_CONFIDENCE_THRESHOLD

            query_text = f"{ticket.subject}\n\n{ticket.description}"
            evidence = await retrieve_evidence(db, query_text, ticket.department_id, k=6)
            evidence = [item for item in evidence if item.source_id != ticket.id][:5]

            features = compute_features(evidence, ticket.ocr_confidence, department_name)
            score = predict_confidence(features)

            ticket.confidence_score = score
            ticket.confidence_features = features.to_dict()
            ticket.confidence_threshold = threshold
            scored += 1

            existing = await db.scalar(
                select(Feedback).where(Feedback.ticket_id == ticket.id, Feedback.reviewer_id == reviewer.id)
            )
            if existing is not None:
                skipped_existing += 1
                continue

            success = simulate_outcome(features, rng)
            db.add(
                Feedback(
                    ticket_id=ticket.id,
                    reviewer_id=reviewer.id,
                    action="accept" if success else "reject",
                    reject_reason=None if success else REJECT_REASON,
                )
            )
            logged += 1

        await db.commit()

    print(f"scored {scored} tickets")
    print(f"logged {logged} new synthetic feedback rows ({skipped_existing} already had one)")


if __name__ == "__main__":
    asyncio.run(main())

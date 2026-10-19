"""Dev-only demo data for the annotation tool v0 (Week 4). Real drafts arrive in Week 5.

Creates one demo reviewer (reviewer@demo.local / Demo@123, pseudonym REV-DEMO) and three
fixture drafts on benchmark tickets from data/benchmark/tickets_v0.jsonl. Everything is
marked benchmark_version="demo" and model="demo-fixture", so it can never be mistaken
for, or mixed with, real drafts or labels. `--clear` removes all of it.

Usage (from backend/):
    uv run python -m app.scripts.seed_annotation_demo [--clear]
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, User

DEMO_VERSION = "demo"
DEMO_EMAIL = "reviewer@demo.local"
TICKETS = Path(__file__).resolve().parents[3] / "data" / "benchmark" / "tickets_v0.jsonl"
KB = Path(__file__).resolve().parents[3] / "data" / "kb"


def _article(article_id: str):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ai"))
    from benchmark.kb import parse_article

    return parse_article(next(KB.glob(f"*/{article_id}.md")))


async def clear(db) -> None:
    drafts = select(Draft.id).where(Draft.benchmark_version == DEMO_VERSION)
    await db.execute(delete(AnnotationAssignment).where(AnnotationAssignment.draft_id.in_(drafts)))
    await db.execute(delete(Draft).where(Draft.benchmark_version == DEMO_VERSION))
    await db.execute(delete(BenchmarkTicket).where(BenchmarkTicket.benchmark_version == DEMO_VERSION))
    user = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is not None:
        await db.execute(delete(Annotator).where(Annotator.user_id == user.id))
        await db.delete(user)
    await db.flush()  # deletes must reach the database before the demo user is re-inserted


async def main() -> None:
    async with SessionLocal() as db:
        await clear(db)
        if "--clear" in sys.argv:
            await db.commit()
            print("demo annotation data removed")
            return

        user = User(email=DEMO_EMAIL, full_name="Demo Reviewer", role="annotator",
                    hashed_password=hash_password("Demo@123"))
        db.add(user)
        await db.flush()
        annotator = Annotator(user_id=user.id, pseudonym="REV-DEMO")
        db.add(annotator)
        await db.flush()

        records = [json.loads(x) for x in TICKETS.read_text(encoding="utf-8").splitlines() if x.strip()]
        picks = [next(r for r in records if r["type"] == t) for t in ("A", "B", "C1")]
        for position, r in enumerate(picks, start=1):
            db.add(BenchmarkTicket(
                id=r["ticket_id"], benchmark_version=DEMO_VERSION, group_id=r["group_id"], subject=r["subject"],
                body=r["body"], attachment_text=r["attachment_text"], department=r["department"],
                priority=r["priority"], type=r["type"], gold_articles=r["gold_articles"], split="demo",
            ))
            await db.flush()
            article = _article(r["gold_articles"][0])
            title, steps_text, steps = article.title, article.sections["Resolution steps"], article.steps[:3]
            draft = Draft(
                benchmark_ticket_id=r["ticket_id"], benchmark_version=DEMO_VERSION, model="demo-fixture",
                prompt_version="demo", schema_valid=True, can_answer=r["type"] != "C1",
                steps=[{"text": s, "citations": [1]} for s in steps], missing_information=[],
                evidence=[{"n": 1, "article_key": r["gold_articles"][0], "title": title, "text": steps_text}],
                raw_text="demo fixture", groundedness=None,
            )
            db.add(draft)
            await db.flush()
            db.add(AnnotationAssignment(draft_id=draft.id, annotator_id=annotator.id, batch="demo", position=position))
        await db.commit()
        print(f"demo reviewer {DEMO_EMAIL} / Demo@123 with {len(picks)} fixture drafts")


if __name__ == "__main__":
    asyncio.run(main())

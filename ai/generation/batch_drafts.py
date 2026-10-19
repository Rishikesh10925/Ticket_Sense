"""Batch-generate cited, claim-checked drafts for every benchmark ticket (Roadmap Week 5
and 6, Shivaganesh).

Runs the same stages as the live pipeline, so offline numbers describe the real system:

    redact -> classify (v2, predicted department) -> hybrid retrieval (logged)
           -> structured draft -> NLI claim check -> drafts + draft_claims rows

Routing uses the classifier's prediction, not the gold department, so routing mistakes
cost what they would cost in production. Every LLM call goes through the response
cache, and tickets that already have a draft for this prompt version are skipped, so an
interrupted run resumes where it stopped.

    python ai/generation/batch_drafts.py --version v1 [--limit 50] [--splits train val]

Checks the benchmark freeze first and refuses to run on changed files.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from benchmark.freeze import verify  # noqa: E402
from generation.drafting import DRAFT_PROMPT_VERSION, Passage, generate_draft  # noqa: E402
from generation.llm import get_llm_client  # noqa: E402
from grounding.claims import check_draft  # noqa: E402
from security.pii import redact  # noqa: E402


def load_tickets(version: str, splits_filter: list[str] | None) -> list[dict]:
    bench = ROOT / "data" / "benchmark"
    tickets = [json.loads(x) for x in (bench / f"benchmark_{version}.jsonl").read_text(encoding="utf-8").splitlines() if x]
    assignment = json.loads((bench / f"splits_{version}.json").read_text(encoding="utf-8"))["assignment"]
    for t in tickets:
        t["split"] = assignment[t["ticket_id"]]
    return [t for t in tickets if not splits_filter or t["split"] in splits_filter]


async def upsert_benchmark(db, tickets: list[dict], version: str) -> None:
    from sqlalchemy.dialects.postgresql import insert

    from app.models.draft import BenchmarkTicket

    rows = [
        {
            "id": t["ticket_id"], "benchmark_version": version, "group_id": t["group_id"],
            "subject": t["subject"], "body": t["body"], "attachment_text": t.get("attachment_text"),
            "department": t["department"], "priority": t["priority"], "type": t["type"],
            "gold_articles": t["gold_articles"], "split": t["split"],
        }
        for t in tickets
    ]
    for i in range(0, len(rows), 500):
        stmt = insert(BenchmarkTicket).values(rows[i:i + 500])
        await db.execute(stmt.on_conflict_do_nothing(index_elements=["id", "benchmark_version"]))
    await db.commit()


async def run(version: str, tickets: list[dict], limit: int | None) -> Counter:
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import Department
    from app.models.draft import Draft, DraftClaim
    from graph.nodes import _classifier_v2, get_scorer
    from retrieval.hybrid import hybrid_search
    from retrieval.run_log import log_run

    client, scorer, classifier = get_llm_client(), get_scorer(), _classifier_v2()
    stats: Counter = Counter()
    async with SessionLocal() as db:
        await upsert_benchmark(db, tickets, version)
        depts = {d.name: d.id for d in await db.scalars(select(Department))}
        done = set(
            await db.scalars(
                select(Draft.benchmark_ticket_id).where(
                    Draft.benchmark_version == version, Draft.prompt_version == DRAFT_PROMPT_VERSION
                )
            )
        )
        todo = [t for t in tickets if t["ticket_id"] not in done][: limit or None]
        print(f"{len(done)} already drafted, {len(todo)} to go", flush=True)
        started = time.perf_counter()
        for i, t in enumerate(todo, start=1):
            mapping: dict[str, str] = {}
            subject = redact(t["subject"], mapping).text
            body = redact(t["body"], mapping).text
            attachment = redact(t.get("attachment_text"), mapping).text or None
            text = f"{subject}\n\n{body}" + (f"\n\n[Extracted from attachment]\n{attachment}" if attachment else "")

            predicted = classifier.predict([text])[0]["department"].label
            stats["routed_correctly" if predicted == t["department"] else "misrouted"] += 1
            result = await hybrid_search(db, text, depts[predicted], k=5)
            run_row = await log_run(db, result, None)
            passages = [Passage(n, h.title, h.text, h.article_key) for n, h in enumerate(result.hits, start=1)]

            draft = await asyncio.to_thread(generate_draft, client, f"{subject}\n\n{body}", attachment, passages)
            grounding = check_draft(draft.steps, {p.n: p.text for p in passages}, scorer) if draft.shown else None
            row = Draft(
                benchmark_ticket_id=t["ticket_id"], benchmark_version=version, retrieval_run_id=run_row.id,
                model=draft.model, prompt_version=draft.prompt_version, schema_valid=draft.schema_valid,
                can_answer=draft.can_answer, steps=draft.steps, missing_information=draft.missing_information,
                evidence=[{"n": p.n, "article_key": p.article_key, "title": p.title, "text": p.text} for p in passages],
                raw_text=draft.raw_text, groundedness=grounding.groundedness if grounding else None,
            )
            row.claims = [
                DraftClaim(step_index=c.step_index, claim_index=c.claim_index, text=c.text, cited=list(c.cited),
                           support=c.support)
                for c in (grounding.claims if grounding else ())
            ]
            db.add(row)
            stats["schema_valid" if draft.schema_valid else f"rejected: {draft.rejection}"] += 1
            stats["shown" if draft.shown else "not_shown"] += 1
            if i % 25 == 0 or i == len(todo):
                await db.commit()
                rate = i / (time.perf_counter() - started) * 60
                print(f"{i}/{len(todo)} drafted ({rate:.1f}/min)", flush=True)
        await db.commit()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--splits", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    problems = verify(args.version)
    if problems:
        raise SystemExit("benchmark changed since the freeze:\n" + "\n".join(problems))
    stats = asyncio.run(run(args.version, load_tickets(args.version, args.splits), args.limit))
    print(json.dumps(dict(stats), indent=2))


if __name__ == "__main__":
    main()

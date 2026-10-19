"""Judge every benchmark draft with the LLM judge (Roadmap Weeks 5 and 7, Shivaganesh).

    python ai/judge/batch_judge.py --version v1 [--limit 50]

The reference comes from the ticket's provenance, never from its type label:

- a served gold article (types A and B): its key facts, plus the B ticket's extra
  question that the article does not cover;
- a withheld gold article (C1): the article exists but the drafter never had it;
- no gold article (C2): nothing to answer from.

The judge model (`llama3.1:8b` by default) is a different model family from the drafter
(`qwen2.5:7b-instruct`), so it does not grade its own writing. Run it after batch
drafting: both models do not fit on an 8 GB GPU together. Resumable; cached.
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

from benchmark.kb import load_articles  # noqa: E402
from generation.llm import get_llm_client  # noqa: E402
from judge.judge import JUDGE_PROMPT_VERSION, Reference, judge  # noqa: E402

JUDGE_MODEL = "llama3.1:8b"


def references(version: str) -> dict[str, Reference]:
    """ticket_id -> Reference, from the frozen benchmark and the KB."""
    articles = {a.id: a for a in load_articles(ROOT / "data" / "kb") if a.id}
    tickets = (ROOT / "data" / "benchmark" / f"benchmark_{version}.jsonl").read_text(encoding="utf-8").splitlines()
    refs = {}
    for line in filter(None, tickets):
        t = json.loads(line)
        gold = articles.get(t["gold_articles"][0]) if t["gold_articles"] else None
        if gold is None:
            refs[t["ticket_id"]] = Reference(kind="none")
        else:
            refs[t["ticket_id"]] = Reference(
                kind="served" if gold.served else "withheld",
                title=gold.meta.get("title"),
                key_facts=tuple(gold.key_facts),
                uncovered_question=t.get("uncovered_question"),
            )
    return refs


async def run(version: str, limit: int | None, model: str) -> Counter:
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import BenchmarkTicket, Draft, JudgeVerdict

    client = get_llm_client(model=model)
    refs = references(version)
    stats: Counter = Counter()
    async with SessionLocal() as db:
        judged = select(JudgeVerdict.draft_id).where(
            JudgeVerdict.model == model, JudgeVerdict.prompt_version == JUDGE_PROMPT_VERSION
        )
        rows = (
            await db.execute(
                select(Draft, BenchmarkTicket)
                .join(
                    BenchmarkTicket,
                    (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                    & (BenchmarkTicket.benchmark_version == Draft.benchmark_version),
                )
                .where(Draft.benchmark_version == version, Draft.id.not_in(judged))
                .order_by(Draft.benchmark_ticket_id)
            )
        ).all()[: limit or None]
        print(f"{len(rows)} drafts to judge with {model}", flush=True)
        started = time.perf_counter()
        for i, (draft, ticket) in enumerate(rows, start=1):
            text = f"{ticket.subject}\n\n{ticket.body}"
            if ticket.attachment_text:
                text += f"\n\n[Attachment]\n{ticket.attachment_text}"
            try:
                v = await asyncio.to_thread(
                    judge, client, text, draft.steps, draft.can_answer, draft.missing_information, refs[ticket.id]
                )
            except (json.JSONDecodeError, KeyError) as exc:
                stats["judge_output_invalid"] += 1
                print(f"{ticket.id}: judge output invalid ({exc})", flush=True)
                continue
            db.add(
                JudgeVerdict(
                    draft_id=draft.id, label=v.label, critical_problem=v.critical_problem,
                    missing_key_facts=list(v.missing_key_facts), contradicted_key_facts=list(v.contradicted_key_facts),
                    rationale=v.rationale, model=v.model, prompt_version=v.prompt_version,
                )
            )
            stats[f"{ticket.type}:{v.label}"] += 1
            if i % 25 == 0 or i == len(rows):
                await db.commit()
                print(f"{i}/{len(rows)} judged ({i / (time.perf_counter() - started) * 60:.1f}/min)", flush=True)
        await db.commit()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=JUDGE_MODEL)
    args = parser.parse_args()
    stats = asyncio.run(run(args.version, args.limit, args.model))
    print(json.dumps(dict(sorted(stats.items())), indent=2))


if __name__ == "__main__":
    main()

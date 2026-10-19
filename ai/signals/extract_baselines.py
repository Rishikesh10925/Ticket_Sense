"""Extract baseline signals B4 to B6 for every benchmark draft into a CSV
(Roadmap Week 6: "compute baseline signals B4, B5 and B6 for all tickets").

    python ai/signals/extract_baselines.py --benchmark-version v1 --out data/signals/baselines_v1.csv

Reads the logged retrieval run of each draft (final rank 1 hit: dense similarity and
reranker score) and the draft's groundedness. Drafts must have been generated with a
logged retrieval run (`drafts.retrieval_run_id`); any without one are reported, not
silently given zeros. Labels are not read here: the evaluation joins them later, so
nothing in this file can leak into the signals.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from signals.baselines import BASELINE_VERSION, DraftSignals  # noqa: E402

FIELDS = ["draft_id", "ticket_id", "group_id", "top1_similarity", "top1_rerank", "groundedness"]

_SQL = """
SELECT d.id::text, d.benchmark_ticket_id, bt.group_id, h.dense_score, h.rerank_score, d.groundedness,
       d.retrieval_run_id IS NOT NULL AS logged
FROM drafts d
JOIN benchmark_tickets bt ON bt.id = d.benchmark_ticket_id AND bt.benchmark_version = d.benchmark_version
LEFT JOIN retrieval_hits h ON h.run_id = d.retrieval_run_id AND h.final_rank = 1
WHERE d.benchmark_version = :version AND d.prompt_version = :prompt_version
ORDER BY d.benchmark_ticket_id
"""


async def extract(version: str, prompt_version: str) -> tuple[list[DraftSignals], list[str]]:
    from sqlalchemy import text

    from app.database import SessionLocal

    async with SessionLocal() as db:
        rows = (await db.execute(text(_SQL), {"version": version, "prompt_version": prompt_version})).all()
    signals, unlogged = [], []
    for draft_id, ticket_id, group_id, dense, rerank, grounded, logged in rows:
        if not logged:
            unlogged.append(ticket_id)
            continue
        signals.append(DraftSignals(draft_id, ticket_id, group_id, dense, rerank, grounded))
    return signals, unlogged


def write_csv(signals: list[DraftSignals], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for s in signals:
            writer.writerow([s.draft_id, s.ticket_id, s.group_id, s.top1_similarity, s.top1_rerank, s.groundedness])


def read_csv(path: Path) -> list[DraftSignals]:
    def num(x: str) -> float | None:
        return float(x) if x not in ("", "None") else None

    with path.open(encoding="utf-8") as f:
        return [
            DraftSignals(r["draft_id"], r["ticket_id"], r["group_id"], num(r["top1_similarity"]),
                         num(r["top1_rerank"]), num(r["groundedness"]))
            for r in csv.DictReader(f)
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--benchmark-version", default="v1")
    parser.add_argument("--prompt-version", default="draft-v1")
    parser.add_argument("--out", default="data/signals/baselines_v1.csv")
    args = parser.parse_args()
    signals, unlogged = asyncio.run(extract(args.benchmark_version, args.prompt_version))
    write_csv(signals, ROOT / args.out)
    print(f"{BASELINE_VERSION}: {len(signals)} drafts -> {args.out}")
    if unlogged:
        print(f"WARNING: {len(unlogged)} drafts have no logged retrieval run, e.g. {unlogged[:3]}")


if __name__ == "__main__":
    main()

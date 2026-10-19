"""Retrieval evaluation against gold provenance (Roadmap Week 4; Blueprint §12.1, §15.1).

For every benchmark ticket, retrieval runs scoped to the ticket's *gold* department
(oracle routing, so retrieval quality is measured separately from classifier errors).
Reports Recall@5, MRR and nDCG@10 for A and B tickets, per configuration:

    keyword        full text only
    dense          vectors only
    fused          reciprocal rank fusion, no rerank
    hybrid         fusion + cross-encoder rerank   (the system)

and two leakage counts that must be zero: hits from another department, and hits from
withheld articles (C1 gold articles must never surface). The locked test split is
excluded unless --include-test is given (Week 10 only).

Usage:
    uv run --project backend python ai/retrieval/evaluate.py \
        --tickets data/benchmark/benchmark_v1.jsonl --splits data/benchmark/splits_v1.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Department, KnowledgeBase  # noqa: E402
from benchmark.splits import file_sha256  # noqa: E402
from evaluation.retrieval_metrics import ndcg_at_k, recall_at_k, reciprocal_rank  # noqa: E402
from retrieval.hybrid import hybrid_search  # noqa: E402

CONFIGS = {
    "keyword": dict(mode="keyword", rerank=False),
    "dense": dict(mode="dense", rerank=False),
    "fused": dict(mode="hybrid", rerank=False),
    "hybrid": dict(mode="hybrid", rerank=True),
}


def ticket_query(r: dict) -> str:
    return f"{r['text']}\n{r.get('attachment_text') or ''}".strip()


async def evaluate(records: list[dict], configs: list[str], k_eval: int = 10) -> dict:
    async with SessionLocal() as db:
        depts = {d.name: d.id for d in await db.scalars(select(Department))}
        articles = {a.article_key: a for a in await db.scalars(select(KnowledgeBase)) if a.article_key}
        withheld = {key for key, a in articles.items() if not a.served}

        report: dict = {}
        for name in configs:
            per_type: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
            leaks = {"cross_department": 0, "withheld": 0}
            probe_by_type: dict[str, list[float]] = defaultdict(list)
            latency: list[float] = []
            for r in records:
                dept_id = depts[r["department"]]
                res = await hybrid_search(db, ticket_query(r), dept_id, k=k_eval, **CONFIGS[name])
                latency.append(sum(res.latency_ms.values()))
                ranked = res.ranked_article_keys()
                for key in ranked:
                    art = articles.get(key)
                    if art is None or art.department_id != dept_id:
                        leaks["cross_department"] += 1
                    if key in withheld:
                        leaks["withheld"] += 1
                if res.probe_top1_similarity is not None:
                    probe_by_type[r["type"]].append(res.probe_top1_similarity)
                if r["type"] in ("A", "B"):
                    gold = r["gold_articles"]
                    m = per_type[r["type"]]
                    m["recall@5"].append(recall_at_k(ranked, gold, 5))
                    m["mrr"].append(reciprocal_rank(ranked, gold))
                    m["ndcg@10"].append(ndcg_at_k(ranked, gold, 10))
            report[name] = {
                "by_type": {
                    t: {metric: round(statistics.mean(v), 4) for metric, v in m.items()} | {"n": len(m["mrr"])}
                    for t, m in sorted(per_type.items())
                },
                "leakage": leaks,
                "probe_top1_mean_by_type": {t: round(statistics.mean(v), 4) for t, v in sorted(probe_by_type.items())},
                "median_latency_ms": round(statistics.median(latency), 1),
            }
            a = report[name]["by_type"].get("A", {})
            print(f"{name:8s} A: R@5 {a.get('recall@5')}  MRR {a.get('mrr')}  nDCG@10 {a.get('ndcg@10')}  "
                  f"leaks {leaks}  median {report[name]['median_latency_ms']} ms", flush=True)
        return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=Path, default=ROOT / "data/benchmark/benchmark_v1.jsonl")
    parser.add_argument("--splits", type=Path, default=ROOT / "data/benchmark/splits_v1.json")
    parser.add_argument("--configs", nargs="*", default=list(CONFIGS))
    parser.add_argument("--include-test", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/retrieval-v1.json")
    args = parser.parse_args()

    records = [json.loads(x) for x in args.tickets.read_text(encoding="utf-8").splitlines() if x.strip()]
    assignment = json.loads(args.splits.read_text(encoding="utf-8"))["assignment"]
    records = [r for r in records if args.include_test or assignment[r["ticket_id"]] != "test"]

    report = asyncio.run(evaluate(records, args.configs))
    report["meta"] = {
        "tickets_sha256": file_sha256(args.tickets),
        "n_tickets": len(records),
        "splits": "all" if args.include_test else "all except locked test",
        "routing": "oracle (gold department)",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

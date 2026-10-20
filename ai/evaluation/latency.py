"""Latency per pipeline stage (Roadmap Week 6, Rishikesh: "record latency per stage").

    python ai/evaluation/latency.py --n 30

Runs the live pipeline's nodes one by one on a seeded sample of validation tickets and
times each stage. The LLM response cache is bypassed, so the draft stage measures real
generation time, and the first ticket is a warm-up (models load) that is not counted.
Run it with the GPU otherwise idle: a concurrent batch job inflates every number.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

STAGES = ("redact", "classify", "route", "retrieve", "draft", "check", "signals")


def summarise(timings: dict[str, list[float]]) -> dict:
    out = {}
    for stage, values in timings.items():
        v = sorted(values)
        out[stage] = {
            "median_ms": round(statistics.median(v), 1),
            "p90_ms": round(v[min(len(v) - 1, int(0.9 * len(v)))], 1),
            "max_ms": round(v[-1], 1),
        }
    return out


async def run(n: int, seed: int) -> dict:
    from app.database import SessionLocal
    from app.models import Department
    from generation.llm import get_llm_client
    from graph.nodes import (get_scorer, make_check_node, make_classify_node, make_draft_node, make_redact_node,
                             make_retrieve_node, make_route_node, make_signals_node)

    bench = ROOT / "data" / "benchmark"
    assignment = json.loads((bench / "splits_v1.json").read_text(encoding="utf-8"))["assignment"]
    tickets = [t for t in map(json.loads, filter(None, (bench / "benchmark_v1.jsonl").read_text(encoding="utf-8").splitlines()))
               if assignment[t["ticket_id"]] == "val"]
    sample = random.Random(seed).sample(tickets, n + 1)

    timings: dict[str, list[float]] = {s: [] for s in STAGES + ("total",)}
    async with SessionLocal() as db:
        nodes = {
            "redact": make_redact_node(), "classify": make_classify_node(),
            "route": make_route_node(db, Department), "retrieve": make_retrieve_node(db),
            "draft": make_draft_node(get_llm_client(cache=False)), "check": make_check_node(get_scorer()),
            "signals": make_signals_node(),
        }
        for k, t in enumerate(sample):
            state = {"subject": t["subject"], "description": t["body"], "attachment_text": t.get("attachment_text")}
            started = time.perf_counter()
            per = {}
            for stage in STAGES:
                t0 = time.perf_counter()
                state |= await nodes[stage](state)
                per[stage] = (time.perf_counter() - t0) * 1000
            per["total"] = (time.perf_counter() - started) * 1000
            await db.rollback()  # retrieval runs from timing are not kept
            if k == 0:
                continue  # warm-up: model loading
            for stage, ms in per.items():
                timings[stage].append(ms)
            print(f"{k}/{n} total {per['total']:.0f} ms", flush=True)
    return {"n": n, "seed": seed, "cache": "bypassed", "stages": summarise(timings)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/latency-v1.json")
    args = parser.parse_args()
    report = asyncio.run(run(args.n, args.seed))
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for stage, m in report["stages"].items():
        print(f"{stage:<9} median {m['median_ms']:>8.1f} ms   p90 {m['p90_ms']:>8.1f} ms")


if __name__ == "__main__":
    main()

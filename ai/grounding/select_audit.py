"""Choose the 100-draft manual groundedness audit and write one worksheet per member
(Blueprint V2 §12.3: "the checker itself is validated on a 100-draft manual audit so
that its errors are known"; Roadmap Weeks 5 and 6, Shivaganesh).

    python ai/grounding/select_audit.py --version v1

Drafts with at least one checked claim, from the non-test splits only (the locked test
is never looked at before Week 10). Stratified by ticket type and by the draft's lowest
claim support (below 0.2, 0.2 to 0.5, 0.5 to 0.9, at least 0.9), so the audit sees the
checker's confident passes, confident failures and the uncertain middle.

Each worksheet row is one claim with its cited passage. The auditor fills `human` with
`supported`, `not_supported` or `unclear`; the NLI score is not shown, so the auditor is
not anchored by it (it stays in the JSON for scoring afterwards).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

AUDIT_SEED = 2026
N_AUDIT = 100
BANDS = ((0.0, 0.2), (0.2, 0.5), (0.5, 0.9), (0.9, 1.01))
MEMBERS = ("R", "A", "S")


def band(min_support: float) -> int:
    return next(i for i, (lo, hi) in enumerate(BANDS) if lo <= min_support < hi)


def stratified(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Round-robin over (type, band) cells so every cell is represented."""
    rng = random.Random(seed)
    cells: dict = defaultdict(list)
    for r in rows:
        cells[(r["type"], band(r["min_support"]))].append(r)
    queues = [sorted(cells[c], key=lambda r: r["draft_id"]) for c in sorted(cells)]
    for q in queues:
        rng.shuffle(q)
    chosen: list[dict] = []
    while len(chosen) < min(n, len(rows)):
        for q in queues:
            if q and len(chosen) < n:
                chosen.append(q.pop())
    return chosen


async def load(version: str) -> list[dict]:
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import BenchmarkTicket, Draft

    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Draft, BenchmarkTicket)
                .join(BenchmarkTicket, (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                      & (BenchmarkTicket.benchmark_version == Draft.benchmark_version))
                .where(Draft.benchmark_version == version, BenchmarkTicket.split != "test")
            )
        ).all()
        out = []
        for draft, ticket in rows:
            await db.refresh(draft, ["claims"])
            if not draft.claims:
                continue
            passages = {e["n"]: e for e in draft.evidence}
            out.append({
                "draft_id": str(draft.id), "ticket_id": ticket.id, "type": ticket.type,
                "ticket": f"{ticket.subject}\n\n{ticket.body}",
                "min_support": min(c.support or 0.0 for c in draft.claims),
                "claims": [
                    {"step": c.step_index + 1, "claim": c.text, "nli_support": c.support,
                     "cited": [{"n": n, "title": passages[n]["title"], "text": passages[n]["text"]}
                               for n in c.cited if n in passages]}
                    for c in sorted(draft.claims, key=lambda c: (c.step_index, c.claim_index))
                ],
            })
        return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "audit")
    args = parser.parse_args()
    chosen = stratified(asyncio.run(load(args.version)), N_AUDIT, AUDIT_SEED)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"audit_sample_{args.version}.json").write_text(
        json.dumps({"seed": AUDIT_SEED, "n": len(chosen), "drafts": chosen}, indent=1) + "\n", encoding="utf-8")
    for m, member in enumerate(MEMBERS):
        with (args.out_dir / f"audit_{args.version}_{member}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draft_id", "ticket_id", "step", "claim", "cited_passages", "human", "note"])
            for d in chosen[m::len(MEMBERS)]:
                for c in d["claims"]:
                    cited = "\n---\n".join(f"[{p['n']}] {p['title']}\n{p['text']}" for p in c["cited"]) or "(cites nothing)"
                    w.writerow([d["draft_id"], d["ticket_id"], c["step"], c["claim"], cited, "", ""])
    counts = defaultdict(int)
    for d in chosen:
        counts[f"{d['type']}/band{band(d['min_support'])}"] += 1
    print(f"{len(chosen)} drafts, {sum(len(d['claims']) for d in chosen)} claims; cells {dict(sorted(counts.items()))}")


if __name__ == "__main__":
    main()

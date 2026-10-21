"""Error analysis of the gate's worst cases (Roadmap Week 9, Shivaganesh).

The worst cases are drafts the gate would show (fast or assisted lane, with the shift
guard) that are labelled unacceptable, ranked by confidence: the higher the score, the
more an engineer would be inclined to trust a wrong draft. For each one the report gives
the ticket, the draft's type, topic and department, the gate's score and top reasons,
the claim-check numbers and the label's rationale, and then counts the failures by
group so patterns show.

    python ai/confidence_model/error_analysis.py --labels judge --top 15

Validation and unseen splits only; the locked test is never read.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

from confidence_model.dataset import load  # noqa: E402
from gate.service import Thresholds, guard_reasons, lane_for  # noqa: E402


async def rationales(draft_ids: list[str]) -> dict[str, tuple[str, str, str]]:
    from sqlalchemy import text

    from app.database import SessionLocal

    async with SessionLocal() as db:
        rows = (await db.execute(text(
            "SELECT DISTINCT ON (d.id) d.id::text, j.label, j.rationale, bt.subject "
            "FROM drafts d JOIN judge_verdicts j ON j.draft_id = d.id "
            "JOIN benchmark_tickets bt ON bt.id = d.benchmark_ticket_id AND bt.benchmark_version = d.benchmark_version "
            "WHERE d.id::text = ANY(:ids) ORDER BY d.id, j.created_at DESC"), {"ids": draft_ids})).all()
    return {r[0]: (r[1], r[2], r[3]) for r in rows}


def main() -> None:
    import joblib

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    bundle = joblib.load(ROOT / "ai" / "confidence_model" / "artifacts" / f"confidence-v1-{args.labels}.joblib")
    model, th = bundle["model"], bundle["thresholds"]
    guard = json.loads((ROOT / "docs" / "results" / f"shift-v1-{args.labels}.json").read_text(encoding="utf-8"))["guard"]
    t = Thresholds("analysis", th["fast"]["threshold"], th["assisted"]["threshold"],
                   guard["min_dept_prob"], guard["min_probe_margin"])

    rows = [r for r in asyncio.run(load("v1", args.labels)) if r.acceptable is not None and r.split in ("val", "unseen")]
    scores = model.predict(rows)
    reasons = model.top_reasons(rows)
    shown_bad = []
    for r, s, why in zip(rows, scores, reasons):
        lane = lane_for(float(s), bool(r.can_answer), t, bool(guard_reasons(r.features, t)))
        if lane != "escalate" and r.acceptable == 0:
            shown_bad.append((float(s), r, lane, why))
    shown_bad.sort(key=lambda x: -x[0])
    worst = shown_bad[: args.top]
    labels = asyncio.run(rationales([r.draft_id for _, r, _, _ in worst]))

    def count(key):
        return dict(Counter(key(r) for _, r, _, _ in shown_bad).most_common())

    lines = [
        f"# Error analysis: worst gate cases ({args.labels} labels)",
        "",
        "PROVISIONAL: labels are the LLM judge's." if args.labels == "judge" else "Human labels.",
        "",
        f"Unacceptable drafts the gate would still show (validation + unseen, guard on): **{len(shown_bad)}**.",
        "",
        "| Group | Counts |",
        "|---|---|",
        f"| Split | {count(lambda r: r.split)} |",
        f"| Ticket type | {count(lambda r: r.type)} |",
        f"| Department | {count(lambda r: r.department)} |",
        f"| Topic | {count(lambda r: r.topic)} |",
        "",
        f"## The {len(worst)} highest-scoring",
        "",
    ]
    for i, (s, r, lane, why) in enumerate(worst, start=1):
        label, rationale, subject = labels.get(r.draft_id, ("?", "", ""))
        f = r.features
        lines += [
            f"### {i}. {r.ticket_id} · {r.type} · {r.department} / {r.topic} · {r.split}",
            f"- Ticket: {subject}",
            f"- Gate: {lane}, score {s:.3f}; reasons: {', '.join(why) or '—'}",
            f"- Claims supported {f.get('gr_supported_share')}, min support {f.get('gr_min_support')}, "
            f"routing certainty {f.get('rt_dept_max_prob')}, probe margin {f.get('rt_probe_margin')}",
            f"- Label {label}: {rationale}",
            "",
        ]
    out = ROOT / "docs" / "results" / f"error-analysis-v1-{args.labels}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))
    print("->", out)


if __name__ == "__main__":
    main()

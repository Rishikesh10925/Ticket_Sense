"""Label agreement (Blueprint V2 §11.6; Roadmap Weeks 7 and 8: "kappa on overlapping
items", exit gate "kappa at least 0.6, or disagreements adjudicated and reported").

    python ai/evaluation/agreement.py

Reports, for whatever labels exist so far:

- reviewers on the overlap set (annotation tool): Cohen's kappa on the four rubric
  labels, linearly weighted kappa (A < M < R < W is ordinal), and kappa on the binary
  acceptable target;
- the team's rubric pilot (`docs/pilot/pilot_v1.csv`): Fleiss' kappa over the members
  who have labelled, and each member against the LLM judge;
- the LLM judge against humans on every draft both labelled (the judge's validation,
  Week 6).

A comparison with fewer than 10 shared items is reported as insufficient, not as a
number.
"""

from __future__ import annotations

import asyncio
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

LABELS = ("A", "M", "R", "W")
MIN_ITEMS = 10


def acceptable(label: str) -> int:
    return int(label in ("A", "M"))


def cohen_kappa(a: list, b: list, weights: str | None = None, categories=LABELS) -> float | None:
    """Cohen's kappa for two raters. `weights="linear"` treats the categories as ordered."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    observed = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        observed[idx[x]][idx[y]] += 1
    n = len(a)
    row = [sum(r) / n for r in observed]
    col = [sum(observed[i][j] for i in range(k)) / n for j in range(k)]

    def w(i, j):
        if weights == "linear":
            return 1 - abs(i - j) / (k - 1)
        return 1.0 if i == j else 0.0

    po = sum(w(i, j) * observed[i][j] / n for i in range(k) for j in range(k))
    pe = sum(w(i, j) * row[i] * col[j] for i in range(k) for j in range(k))
    return None if pe == 1 else round((po - pe) / (1 - pe), 4)


def fleiss_kappa(items: list[list[str]], categories=LABELS) -> float | None:
    """Fleiss' kappa; every item rated by the same number (>= 2) of raters."""
    if not items or len({len(r) for r in items}) != 1 or len(items[0]) < 2:
        return None
    n, raters = len(items), len(items[0])
    counts = [[r.count(c) for c in categories] for r in items]
    p_j = [sum(c[j] for c in counts) / (n * raters) for j in range(len(categories))]
    p_i = [(sum(x * x for x in c) - raters) / (raters * (raters - 1)) for c in counts]
    p_bar, pe = sum(p_i) / n, sum(p * p for p in p_j)
    return None if pe == 1 else round((p_bar - pe) / (1 - pe), 4)


def pair_report(a: list[str], b: list[str]) -> dict:
    if len(a) < MIN_ITEMS:
        return {"n": len(a), "status": f"insufficient (< {MIN_ITEMS} shared items)"}
    return {
        "n": len(a),
        "raw_agreement": round(sum(x == y for x, y in zip(a, b)) / len(a), 4),
        "kappa": cohen_kappa(a, b),
        "kappa_linear": cohen_kappa(a, b, weights="linear"),
        "acceptable_agreement": round(sum(acceptable(x) == acceptable(y) for x, y in zip(a, b)) / len(a), 4),
        "kappa_acceptable": cohen_kappa([str(acceptable(x)) for x in a], [str(acceptable(y)) for y in b],
                                        categories=("0", "1")),
    }


def pilot(path: Path, judge: dict[str, str]) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    members = [m for m in ("R", "A", "S") if any(r[f"label_{m}"] for r in rows)]
    complete = [[r[f"label_{m}"] for m in members] for r in rows if all(r[f"label_{m}"] for m in members)]
    out = {"members_labelled": members,
           "fleiss_kappa": fleiss_kappa(complete) if len(members) >= 2 else f"needs >= 2 members, has {len(members)}"}
    for m in members:
        pairs = [(r[f"label_{m}"], judge[r["draft_id"]]) for r in rows if r[f"label_{m}"] and r["draft_id"] in judge]
        out[f"{m}_vs_judge"] = pair_report([p[0] for p in pairs], [p[1] for p in pairs])
    return out


async def from_database() -> tuple[dict, dict[str, str]]:
    from sqlalchemy import text

    from app.database import SessionLocal

    async with SessionLocal() as db:
        judge = dict((await db.execute(text(
            "SELECT DISTINCT ON (draft_id) draft_id::text, label FROM judge_verdicts ORDER BY draft_id, created_at DESC"
        ))).all())
        rows = (await db.execute(text(
            "SELECT a.draft_id::text, an.pseudonym, l.label FROM labels l "
            "JOIN annotation_assignments a ON a.id = l.assignment_id JOIN annotators an ON an.id = a.annotator_id "
            "WHERE a.overlap AND l.label IS NOT NULL AND a.batch NOT LIKE 'adjud%%'"
        ))).all()
    by_draft: dict[str, list[str]] = {}
    for draft_id, _, label in rows:
        by_draft.setdefault(draft_id, []).append(label)
    pairs = [v[:2] for v in by_draft.values() if len(v) >= 2]
    human_all = {d: v[0] for d, v in by_draft.items()}
    shared = [(human_all[d], judge[d]) for d in human_all if d in judge]
    reviewers = {
        "overlap_pairs": pair_report([p[0] for p in pairs], [p[1] for p in pairs]),
        "judge_vs_reviewers": pair_report([s[0] for s in shared], [s[1] for s in shared]),
        "label_counts": dict(Counter(label for _, _, label in rows)),
    }
    return reviewers, judge


def main() -> None:
    reviewers, judge = asyncio.run(from_database())
    report = {"reviewers": reviewers, "pilot": pilot(ROOT / "docs" / "pilot" / "pilot_v1.csv", judge)}
    out = ROOT / "docs" / "results" / "agreement-v1.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()

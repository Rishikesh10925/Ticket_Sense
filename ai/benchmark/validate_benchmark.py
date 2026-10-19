"""Benchmark validation (Roadmap Week 3: "gold articles exist, no group overlap across
splits, withheld topics respected"). The Week 3 exit gate needs this to be green before
the benchmark is frozen.

Usage:
    uv run --project backend python ai/benchmark/validate_benchmark.py \
        data/benchmark/benchmark_v1.jsonl data/benchmark/splits_v1.json [--require-review]

Exit code 0 when every check passes. KB human review is reported as its own line; with
--require-review an unreviewed article fails the run (the final freeze uses it).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.generate_tickets import TYPE_SHARES  # noqa: E402
from benchmark.kb import Article, load_articles, review_status  # noqa: E402
from benchmark.splits import check_manifest, file_sha256  # noqa: E402

SHARE_TOLERANCE = 0.03
REQUIRED = ("ticket_id", "group_id", "text", "department", "priority", "type", "gold_articles", "difficulty")


def validate(records: list[dict], articles: list[Article], manifest: dict | None, tickets_path: Path | None) -> list[str]:
    problems: list[str] = []
    by_id = {a.id: a for a in articles if a.is_v2}

    ids = [r.get("ticket_id") for r in records]
    if len(ids) != len(set(ids)):
        problems.append("duplicate ticket_id values")

    texts = Counter(" ".join(r.get("text", "").lower().split()) for r in records)
    dupes = sum(c - 1 for c in texts.values() if c > 1)
    if dupes:
        problems.append(f"{dupes} tickets duplicate another ticket's text exactly")

    groups: dict[str, set] = defaultdict(set)
    for r in records:
        missing = [k for k in REQUIRED if k not in r]
        if missing:
            problems.append(f"{r.get('ticket_id')}: missing fields {missing}")
            continue
        t, gold = r["type"], r["gold_articles"]
        groups[r["group_id"]].add((t, r["department"], tuple(gold)))
        if t == "C2":
            if gold:
                problems.append(f"{r['ticket_id']}: C2 ticket has gold articles")
            continue
        if not gold:
            problems.append(f"{r['ticket_id']}: {t} ticket has no gold article")
            continue
        for gid in gold:
            art = by_id.get(gid)
            if art is None:
                problems.append(f"{r['ticket_id']}: gold article {gid} does not exist")
                continue
            if art.meta.get("department") != r["department"]:
                problems.append(f"{r['ticket_id']}: department {r['department']} != article {gid}")
            if t in ("A", "B") and not art.served:
                problems.append(f"{r['ticket_id']}: {t} ticket built on withheld article {gid}")
            if t == "C1" and art.served:
                problems.append(f"{r['ticket_id']}: C1 ticket built on served article {gid}")
        if t == "B" and not r.get("uncovered_question"):
            problems.append(f"{r['ticket_id']}: B ticket without uncovered_question")

    for gid, variants in groups.items():
        if len(variants) > 1:
            problems.append(f"group {gid} mixes types, departments or gold articles")

    counts = Counter(r.get("type") for r in records)
    for t, share in TYPE_SHARES.items():
        actual = counts.get(t, 0) / max(1, len(records))
        if abs(actual - share) > SHARE_TOLERANCE:
            problems.append(f"type {t} is {actual:.1%} of tickets, target {share:.0%}")

    if manifest is not None:
        if tickets_path is not None and manifest.get("tickets_sha256") != file_sha256(tickets_path):
            problems.append("split manifest hash does not match the tickets file")
        problems.extend(check_manifest(records, manifest.get("assignment", {})))
        extra = set(manifest.get("assignment", {})) - set(ids)
        if extra:
            problems.append(f"manifest lists {len(extra)} ticket ids not in the tickets file")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tickets", type=Path)
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--require-review", action="store_true")
    args = parser.parse_args()

    records = [json.loads(line) for line in args.tickets.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
    articles = load_articles()
    problems = validate(records, articles, manifest, args.tickets)

    n_v2, n_reviewed = review_status(articles)
    review_ok = n_reviewed == n_v2 and n_v2 > 0
    print(f"{len(records)} tickets, types {dict(sorted(Counter(r['type'] for r in records).items()))}")
    print(f"KB human review: {n_reviewed}/{n_v2} articles reviewed" + ("" if review_ok else "  [PENDING]"))
    if args.require_review and not review_ok:
        problems.append("KB articles not all human-reviewed (--require-review)")
    for p in problems:
        print("FAIL", p)
    print("validation GREEN" if not problems else f"validation RED ({len(problems)} problems)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())

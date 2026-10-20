"""Write or verify the benchmark freeze record (Roadmap Week 3; Blueprint V2 §11).

The record pins everything the results depend on: hashes of the tickets, the split
manifest, the taxonomy and every KB article, the generator prompt version and model,
the counts, and how many articles were human-reviewed at freeze time.

    python ai/benchmark/freeze.py write  --version v1   # after generation and validation
    python ai/benchmark/freeze.py verify --version v1   # before any evaluation run
    python ai/benchmark/freeze.py amend --version v1 --articles SAP-PO-002 --reason "..."

`amend` records a knowledge-base correction after the freeze (the pre-registration's
standing rule): the changed articles, the reason and the new KB hash, in
FREEZE_<version>_amend<n>.json. Earlier records are never edited. Tickets and splits
must be unchanged; `verify` then checks the KB against the latest amendment.

`verify` exits non-zero if any frozen file changed, so a silently edited ticket or
article cannot reach a reported number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from benchmark.generate_tickets import PROMPT_VERSION  # noqa: E402
from benchmark.kb import ai_review_count, load_articles, review_status  # noqa: E402
from benchmark.splits import file_sha256  # noqa: E402


def _paths(version: str) -> dict[str, Path]:
    bench = ROOT / "data" / "benchmark"
    return {
        "tickets": bench / f"benchmark_{version}.jsonl",
        "splits": bench / f"splits_{version}.json",
        "taxonomy": ROOT / "data" / "taxonomy.yaml",
        "record": bench / f"FREEZE_{version}.json",
    }


def article_sha256(path: Path) -> str:
    """Content hash of one article, ignoring the `reviewer:` line: recording a human
    fact-check is not a content change, but any edit it leads to is."""
    lines = path.read_bytes().replace(b"\r\n", b"\n").split(b"\n")
    return hashlib.sha256(b"\n".join(line for line in lines if not line.startswith(b"reviewer:"))).hexdigest()


def kb_hashes() -> dict[str, str]:
    kb = ROOT / "data" / "kb"
    return {p.relative_to(kb).as_posix(): article_sha256(p) for p in sorted(kb.rglob("*.md"))}


def combined(hashes: dict[str, str]) -> str:
    return hashlib.sha256("\n".join(f"{k} {v}" for k, v in sorted(hashes.items())).encode()).hexdigest()


def build_record(version: str, model: str, rejected: int | None, dropped: int | None) -> dict:
    p = _paths(version)
    tickets = [json.loads(line) for line in p["tickets"].read_text(encoding="utf-8").splitlines() if line.strip()]
    splits = json.loads(p["splits"].read_text(encoding="utf-8"))
    articles = load_articles(ROOT / "data" / "kb")
    total, reviewed = review_status(articles)
    kb = kb_hashes()
    return {
        "benchmark_version": version,
        "frozen_on": date.today().isoformat(),
        "status": "final" if reviewed == total else f"provisional: {reviewed}/{total} KB articles human-reviewed",
        "generator": {"prompt_version": PROMPT_VERSION, "model": model, "attempts_rejected": rejected,
                      "paraphrases_dropped": dropped},
        "counts": {
            "tickets": len(tickets),
            "scenarios": len({t["group_id"] for t in tickets}),
            "by_type": dict(sorted(Counter(t["type"] for t in tickets).items())),
            "by_department": dict(sorted(Counter(t["department"] for t in tickets).items())),
            "by_split": splits["counts"],
            "with_attachment": sum(1 for t in tickets if t.get("attachment_text")),
        },
        "kb": {"articles": total, "reviewed": reviewed, "ai_checked_only": ai_review_count(articles),
               "combined_sha256": combined(kb)},
        "sha256": {
            "tickets": file_sha256(p["tickets"]),
            "splits": file_sha256(p["splits"]),
            "taxonomy": file_sha256(p["taxonomy"]),
        },
        "split_seed": splits["seed"],
    }


def amendments(version: str) -> list[Path]:
    bench = ROOT / "data" / "benchmark"
    return sorted(bench.glob(f"FREEZE_{version}_amend*.json"), key=lambda q: int(q.stem.rsplit("amend", 1)[1]))


def amend(version: str, articles: list[str], reason: str) -> dict:
    p = _paths(version)
    record = json.loads(p["record"].read_text(encoding="utf-8"))
    for name in ("tickets", "splits", "taxonomy"):
        if file_sha256(p[name]) != record["sha256"][name]:
            raise SystemExit(f"{name} changed too: an amendment may only correct KB articles")
    loaded = load_articles(ROOT / "data" / "kb")
    known = {a.id for a in loaded}
    unknown = [a for a in articles if a not in known]
    if unknown:
        raise SystemExit(f"unknown articles: {unknown}")
    total, reviewed = review_status(loaded)
    n = len(amendments(version)) + 1
    entry = {
        "benchmark_version": version,
        "amendment": n,
        "date": date.today().isoformat(),
        "changed_articles": sorted(articles),
        "reason": reason,
        "tickets_unchanged": True,
        "kb": {"articles": total, "reviewed": reviewed, "ai_checked_only": ai_review_count(loaded),
               "combined_sha256": combined(kb_hashes())},
    }
    out = p["record"].with_name(f"FREEZE_{version}_amend{n}.json")
    out.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    return entry


def verify(version: str) -> list[str]:
    p = _paths(version)
    record = json.loads(p["record"].read_text(encoding="utf-8"))
    latest = amendments(version)
    if latest:
        record["kb"] = json.loads(latest[-1].read_text(encoding="utf-8"))["kb"]
    problems = []
    for name in ("tickets", "splits", "taxonomy"):
        if file_sha256(p[name]) != record["sha256"][name]:
            problems.append(f"{p[name].relative_to(ROOT).as_posix()} changed since the freeze")
    if combined(kb_hashes()) != record["kb"]["combined_sha256"]:
        problems.append("the knowledge base changed since the freeze (amend the pre-registration and refreeze)")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cmd", choices=["write", "verify", "amend"])
    parser.add_argument("--articles", nargs="*", default=[], help="amend: the corrected article ids")
    parser.add_argument("--reason", default="", help="amend: why they were corrected")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--model", default="qwen2.5:7b-instruct")
    parser.add_argument("--rejected", type=int, default=None, help="generator's rejected-attempt count")
    parser.add_argument("--dropped", type=int, default=None, help="generator's dropped-paraphrase count")
    args = parser.parse_args()
    if args.cmd == "write":
        record = build_record(args.version, args.model, args.rejected, args.dropped)
        _paths(args.version)["record"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
    elif args.cmd == "amend":
        if not args.articles or not args.reason:
            raise SystemExit("amend needs --articles and --reason")
        print(json.dumps(amend(args.version, args.articles, args.reason), indent=2))
    else:
        problems = verify(args.version)
        print("\n".join(problems) if problems else f"benchmark {args.version}: frozen files unchanged")
        sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

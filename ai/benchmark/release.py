"""Package the benchmark for release (Roadmap Week 12, Shivaganesh: "package the
benchmark release with datasheet"; Blueprint V2 §22 "open benchmark release with
datasheet and model card").

    python ai/benchmark/release.py              # -> release/ticketsense-benchmark-v1.zip

The zip holds the frozen tickets, splits and freeze records, the knowledge base, the
red-team set, the datasheet and the labelling rubric, a README and SHA256SUMS. It is
byte-for-byte reproducible (sorted entries, fixed timestamps) and is built only if the
freeze still verifies, so a release can never differ from what the experiments used.
No labels are included: human labels do not exist yet and LLM-judge labels are not results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

FIXED_TIME = (2026, 10, 19, 0, 0, 0)  # the freeze date


def contents(version: str) -> dict[str, Path]:
    """Archive path -> source file."""
    files = {
        f"benchmark/benchmark_{version}.jsonl": ROOT / "data" / "benchmark" / f"benchmark_{version}.jsonl",
        f"benchmark/splits_{version}.json": ROOT / "data" / "benchmark" / f"splits_{version}.json",
        "redteam/injection_v1.jsonl": ROOT / "data" / "redteam" / "injection_v1.jsonl",
        "docs/datasheet.md": ROOT / "docs" / "datasheet.md",
        "docs/labelling-rubric.md": ROOT / "docs" / "labelling-rubric.md",
    }
    for record in sorted((ROOT / "data" / "benchmark").glob(f"FREEZE_{version}*.json")):
        files[f"benchmark/{record.name}"] = record
    for article in sorted((ROOT / "data" / "kb").rglob("*.md")):
        files[f"kb/{article.relative_to(ROOT / 'data' / 'kb').as_posix()}"] = article
    return files


def readme(version: str, record: dict) -> str:
    c = record["counts"]
    types = ", ".join(f"{k} {v}" for k, v in c["by_type"].items())
    splits = ", ".join(f"{k} {v}" for k, v in c["by_split"].items())
    return f"""# TicketSense Benchmark {version}

Synthetic IT and HR helpdesk tickets with known provenance, for evaluating whether a
support system can decide when an AI-drafted reply deserves to be shown.

- Tickets: {c['tickets']} from {c['scenarios']} scenarios; types {types}
- Splits (grouped by gold article): {splits}
- Knowledge base: the articles under `kb/`, five departments
- Frozen on {record['frozen_on']}; status: {record['status']}
- Red team: 40 prompt-injection tickets (`redteam/injection_v1.jsonl`)

Read `docs/datasheet.md` before use: it covers motivation, composition, collection,
intended uses and limitations. Ticket types: A answerable from one article, B answerable
plus one question it cannot answer, C1 written from a withheld article (unseen topic),
C2 vague or out of scope.

Integrity: `SHA256SUMS` lists every file; `benchmark/FREEZE_{version}.json` records the
hashes the experiments used.

License: **To be decided by the authors before publication.**
"""


def build(version: str, out_dir: Path) -> Path:
    from benchmark.freeze import verify

    problems = verify(version)
    if problems:
        raise SystemExit("freeze does not verify; refusing to release:\n" + "\n".join(problems))
    files = contents(version)
    record = json.loads(files[f"benchmark/FREEZE_{version}.json"].read_text(encoding="utf-8"))
    payload = {name: path.read_bytes() for name, path in sorted(files.items())}
    payload["README.md"] = readme(version, record).encode("utf-8")
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(payload.items()))
    payload["SHA256SUMS"] = sums.encode("utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"ticketsense-benchmark-{version}.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(payload):
            info = zipfile.ZipInfo(f"ticketsense-benchmark-{version}/{name}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, payload[name])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    out = build(args.version, args.out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}  {out.stat().st_size // 1024} KB  sha256 {digest}")


if __name__ == "__main__":
    main()

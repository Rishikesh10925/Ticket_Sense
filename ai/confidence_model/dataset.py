"""Training and evaluation rows for the confidence model (Blueprint V2 §13; Roadmap
Week 8, Shivaganesh).

One row per benchmark draft: its signal vector (features-v1, plus the model-side
signals where computed), its provenance (type, department, topic, scenario group,
split) and an `acceptable` label from one named source:

    human   reviewers' labels (annotation tool); headline numbers use only these
    judge   the LLM judge's labels; training volume and pipeline development only

The locked test split is never returned unless `include_test=True`, and every such
access is appended to data/annotation/locked_test_access.log (Week 8: "record every
access"). Development before Week 10 never sets it.

Rows come from the database, or (Week 10, fresh-clone reproduction) from the committed
export `data/eval/eval_inputs_<version>.jsonl.gz` when `TS_EVAL_SOURCE=file`. The export
holds every split except the locked test, so a clone can rebuild all development tables
without the database or a GPU, and still cannot see the locked test:

    python ai/confidence_model/dataset.py export
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

LABEL_SOURCES = ("human", "judge")
ACCESS_LOG = ROOT / "data" / "annotation" / "locked_test_access.log"
EXPORT_DIR = ROOT / "data" / "eval"


@dataclass
class Row:
    draft_id: str
    ticket_id: str
    group_id: str
    type: str
    department: str
    topic: str
    split: str
    can_answer: bool | None
    features: dict
    acceptable: int | None
    extra: dict = field(default_factory=dict)  # model-side baseline values (B1, B2, B3)


def _topics(version: str) -> dict[str, str]:
    from benchmark.kb import load_articles

    topic = {a.id: a.meta.get("topic") or "none" for a in load_articles(ROOT / "data" / "kb") if a.id}
    tickets = (ROOT / "data" / "benchmark" / f"benchmark_{version}.jsonl").read_text(encoding="utf-8").splitlines()
    out = {}
    for line in filter(None, tickets):
        t = json.loads(line)
        out[t["ticket_id"]] = topic.get(t["gold_articles"][0], "none") if t["gold_articles"] else "none"
    return out


_SQL = """
SELECT d.id::text, bt.id, bt.group_id, bt.type, bt.department, bt.split, d.can_answer,
       sv.features, ms.features,
       (SELECT j.acceptable FROM judge_verdicts j WHERE j.draft_id = d.id ORDER BY j.created_at DESC LIMIT 1),
       (SELECT avg(CASE WHEN l.acceptable THEN 1.0 ELSE 0.0 END)
          FROM annotation_assignments a JOIN labels l ON l.assignment_id = a.id
         WHERE a.draft_id = d.id AND l.label IS NOT NULL AND a.batch NOT LIKE 'adjud%%'),
       (SELECT CASE WHEN l.acceptable THEN 1 ELSE 0 END
          FROM annotation_assignments a JOIN labels l ON l.assignment_id = a.id
         WHERE a.draft_id = d.id AND l.label IS NOT NULL AND a.batch LIKE 'adjud%%'
         ORDER BY l.created_at DESC LIMIT 1)
FROM drafts d
JOIN benchmark_tickets bt ON bt.id = d.benchmark_ticket_id AND bt.benchmark_version = d.benchmark_version
JOIN signal_vectors sv ON sv.draft_id = d.id AND sv.feature_version = 'features-v1'
LEFT JOIN signal_vectors ms ON ms.draft_id = d.id AND ms.feature_version = 'model-signals-v1'
WHERE d.benchmark_version = :version AND d.prompt_version = :prompt_version
"""


def human_label(mean_acceptable: float | None, adjudicated: int | None) -> int | None:
    """One reviewer: their label. Two that agree: that label. Two that disagree: the
    adjudicator's label, or no label until adjudication (docs/annotation-tool.md)."""
    if mean_acceptable is None:
        return None
    if mean_acceptable in (0.0, 1.0):
        return int(mean_acceptable)
    return adjudicated


def verify_inputs(version: str) -> None:
    """Refuse to train or evaluate on changed data (Roadmap Week 8: "verify the
    locked-test data hash"): the benchmark freeze must verify and the sealed locked-test
    selection must still match its hash."""
    import hashlib

    from benchmark.freeze import verify

    problems = verify(version)
    seal = json.loads((ROOT / "data" / "annotation" / "locked_test_seal.json").read_text(encoding="utf-8"))
    selection = json.loads((ROOT / "data" / "annotation" / f"selection_{version}.json").read_text(encoding="utf-8"))
    ids = sorted(selection["selected"]["test"])
    if hashlib.sha256("\n".join(ids).encode()).hexdigest() != seal["ticket_ids_sha256"]:
        problems.append("the locked-test selection no longer matches its seal")
    if problems:
        raise RuntimeError("inputs changed since they were frozen or sealed:\n" + "\n".join(problems))


async def _records_db(version: str) -> list[tuple]:
    from sqlalchemy import text

    from app.database import SessionLocal
    from generation.drafting import DRAFT_PROMPT_VERSION

    async with SessionLocal() as db:
        result = await db.execute(text(_SQL), {"version": version, "prompt_version": DRAFT_PROMPT_VERSION})
        return [tuple(r) for r in result.all()]


def export_path(version: str) -> Path:
    return EXPORT_DIR / f"eval_inputs_{version}.jsonl.gz"


def _records_file(version: str) -> list[tuple]:
    path = export_path(version)
    meta = json.loads(path.with_suffix("").with_suffix(".json").read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
        raise RuntimeError(f"{path.name} does not match its recorded hash")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [tuple(json.loads(line)) for line in f if line.strip()]


async def export(version: str = "v1") -> Path:
    """Write the non-test rows to a deterministic gzip file plus a hash sidecar."""
    records = sorted((r for r in await _records_db(version) if r[5] != "test"), key=lambda r: r[0])
    lines = [json.dumps([None if v is None else (float(v) if k == 10 else v) for k, v in enumerate(r)],
                        sort_keys=True) for r in records]
    path = export_path(version)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
        f.write(("\n".join(lines) + "\n").encode("utf-8"))
    meta = {"what": "evaluation inputs without the locked test (confidence_model/dataset.py export)",
            "version": version, "rows": len(lines), "splits": sorted({r[5] for r in records}),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    path.with_suffix("").with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    return path


async def load(version: str = "v1", label_source: str = "judge", include_test: bool = False,
               reason: str | None = None) -> list[Row]:
    if label_source not in LABEL_SOURCES:
        raise ValueError(f"label_source must be one of {LABEL_SOURCES}")
    verify_inputs(version)
    if include_test:
        if not reason:
            raise ValueError("reading the locked test needs a recorded reason")
        ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACCESS_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}\t{label_source}\t{reason}\n")

    from_file = os.environ.get("TS_EVAL_SOURCE", "db") == "file"
    if from_file and include_test:
        raise ValueError("the locked test is not in the export; the final evaluation reads the database")
    topics = _topics(version)
    records = _records_file(version) if from_file else await _records_db(version)
    rows = []
    for (draft_id, ticket_id, group_id, typ, dept, split, can_answer, features, model_side,
         judge_ok, human_mean, adjudicated) in records:
        if split == "test" and not include_test:
            continue
        label = (int(judge_ok) if judge_ok is not None else None) if label_source == "judge" \
            else human_label(float(human_mean) if human_mean is not None else None, adjudicated)
        model_side = dict(model_side or {})
        features = dict(features)
        if model_side.get("b3_claim_agreement") is not None:
            features["cs_agreement"] = model_side["b3_claim_agreement"]  # consistency group (§13.2)
        rows.append(Row(draft_id, ticket_id, group_id, typ, dept, topics.get(ticket_id, "none"), split,
                        can_answer, features, label, model_side))
    # One fixed order whatever the source: row order sets the cross-validation folds and
    # XGBoost's subsampling, and the database returns rows in storage order (Week 10
    # fresh-clone test: the same rows in another order gave different tables).
    return sorted(rows, key=lambda r: r.draft_id)


if __name__ == "__main__":
    import asyncio

    if sys.argv[1:] != ["export"]:
        raise SystemExit("usage: python ai/confidence_model/dataset.py export")
    print("->", asyncio.run(export("v1")))

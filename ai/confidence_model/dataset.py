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
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai"))

LABEL_SOURCES = ("human", "judge")
ACCESS_LOG = ROOT / "data" / "annotation" / "locked_test_access.log"


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


async def load(version: str = "v1", label_source: str = "judge", include_test: bool = False,
               reason: str | None = None) -> list[Row]:
    from sqlalchemy import text

    from app.database import SessionLocal
    from generation.drafting import DRAFT_PROMPT_VERSION

    if label_source not in LABEL_SOURCES:
        raise ValueError(f"label_source must be one of {LABEL_SOURCES}")
    if include_test:
        if not reason:
            raise ValueError("reading the locked test needs a recorded reason")
        ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACCESS_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}\t{label_source}\t{reason}\n")

    topics = _topics(version)
    async with SessionLocal() as db:
        result = await db.execute(text(_SQL), {"version": version, "prompt_version": DRAFT_PROMPT_VERSION})
        records = result.all()
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
    return rows

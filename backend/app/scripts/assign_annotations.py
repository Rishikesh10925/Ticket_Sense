"""Create a labelling batch, or the adjudication batch, from the planner
(app/services/assignments.py; docs/annotation-tool.md).

    # Sprint 1: label these drafts, 150 of them twice, shuffled per reviewer.
    python -m app.scripts.assign_annotations plan --batch sprint1 \
        --drafts data/annotation/sprint1_drafts.txt --overlap 150 --seed 2026

    # After a sprint: overlap drafts whose two labels disagree on acceptable -> a third reviewer.
    python -m app.scripts.assign_annotations adjudicate --batch adjud1 --seed 2026

`--drafts` is a text file of draft ids, one per line (the stratified selection, Week 7).
Strata come from the benchmark ticket's type and department. Only active annotators are
used. The batch, seed and counts are written to data/annotation/<batch>.json so the
plan can be regenerated exactly.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from collections import defaultdict
from pathlib import Path

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.annotation import AnnotationAssignment, Annotator, Label
from app.models.draft import BenchmarkTicket, Draft
from app.services.assignments import plan_adjudications, plan_assignments

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_DIR = ROOT / "data" / "annotation"


async def _active_annotators(db) -> list[uuid.UUID]:
    """Active reviewers, never the dev-only demo account (seed_annotation_demo, @demo.local):
    it must not receive real labelling work (Week 12)."""
    from app.models import User

    return list(await db.scalars(
        select(Annotator.id).join(User, User.id == Annotator.user_id)
        .where(Annotator.active.is_(True), ~User.email.endswith("@demo.local"))
        .order_by(Annotator.pseudonym)
    ))


async def _next_positions(db) -> tuple[dict, dict]:
    rows = (
        await db.execute(
            select(AnnotationAssignment.annotator_id, func.count(), func.max(AnnotationAssignment.position)).group_by(
                AnnotationAssignment.annotator_id
            )
        )
    ).all()
    return {a: n for a, n, _ in rows}, {a: (p or 0) + 1 for a, _, p in rows}


async def plan(batch: str, drafts_file: Path, n_overlap: int, seed: int) -> dict:
    ids = [uuid.UUID(line.strip()) for line in drafts_file.read_text().splitlines() if line.strip()]
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Draft.id, BenchmarkTicket.type, BenchmarkTicket.department)
                .join(
                    BenchmarkTicket,
                    (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                    & (BenchmarkTicket.benchmark_version == Draft.benchmark_version),
                )
                .where(Draft.id.in_(ids))
            )
        ).all()
        missing = set(ids) - {r[0] for r in rows}
        if missing:
            raise SystemExit(f"{len(missing)} draft ids are not benchmark drafts, e.g. {sorted(missing, key=str)[0]}")
        annotators = await _active_annotators(db)
        _, offset = await _next_positions(db)
        planned = plan_assignments([(r[0], f"{r[1]}|{r[2]}") for r in rows], annotators, n_overlap, seed)
        for a in planned:
            db.add(
                AnnotationAssignment(
                    draft_id=a.draft_id,
                    annotator_id=a.annotator_id,
                    batch=batch,
                    overlap=a.overlap,
                    # Later batches queue after anything a reviewer already has.
                    position=offset.get(a.annotator_id, 1) - 1 + a.position,
                )
            )
        await db.commit()
    per_annotator = defaultdict(int)
    for a in planned:
        per_annotator[str(a.annotator_id)] += 1
    return {
        "batch": batch,
        "kind": "plan",
        "seed": seed,
        "drafts": len(ids),
        "overlap": n_overlap,
        "assignments": len(planned),
        "per_annotator": dict(per_annotator),
    }


async def adjudicate(batch: str, seed: int) -> dict:
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(AnnotationAssignment.draft_id, AnnotationAssignment.annotator_id, Label.acceptable)
                .join(Label, Label.assignment_id == AnnotationAssignment.id)
                .where(AnnotationAssignment.overlap.is_(True), Label.label.is_not(None))
            )
        ).all()
        by_draft: dict = defaultdict(list)
        for draft_id, annotator_id, acceptable in rows:
            by_draft[draft_id].append((annotator_id, acceptable))
        disagreements = [
            (d, [a for a, _ in labels])
            for d, labels in by_draft.items()
            if len(labels) == 2 and labels[0][1] != labels[1][1]
        ]
        load, positions = await _next_positions(db)
        planned = plan_adjudications(disagreements, await _active_annotators(db), load, positions, seed)
        for a in planned:
            db.add(
                AnnotationAssignment(
                    draft_id=a.draft_id, annotator_id=a.annotator_id, batch=batch, overlap=True, position=a.position
                )
            )
        await db.commit()
    return {"batch": batch, "kind": "adjudication", "seed": seed, "disagreements": len(disagreements)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create labelling assignments")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--batch", required=True)
    p.add_argument("--drafts", required=True, type=Path)
    p.add_argument("--overlap", type=int, default=150)
    p.add_argument("--seed", type=int, default=2026)
    a = sub.add_parser("adjudicate")
    a.add_argument("--batch", required=True)
    a.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    if args.cmd == "plan":
        manifest = asyncio.run(plan(args.batch, args.drafts, args.overlap, args.seed))
    else:
        manifest = asyncio.run(adjudicate(args.batch, args.seed))
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out = MANIFEST_DIR / f"{args.batch}.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

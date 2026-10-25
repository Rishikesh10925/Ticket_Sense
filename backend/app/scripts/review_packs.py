"""Offline labelling for outside reviewers (Roadmap Week 12; docs/annotation-tool.md).

Reviewers label on their own laptops without reaching this machine: each gets one HTML
file (a "review pack") with exactly what the /annotate screen shows (ticket, draft,
evidence; never score, lane, model, type, split or overlap) and sends back one CSV.

    python -m app.scripts.review_packs add --names Asha Ravi Meena Kiran Divya
    python -m app.scripts.review_packs selection
    python -m app.scripts.assign_annotations plan --batch sprint1 \
        --drafts data/annotation/selection_v1_drafts.txt --overlap 150 --seed 2026
    python -m app.scripts.review_packs export
    python -m app.scripts.review_packs import data/annotation/returned/labels_REV-01.csv
    python -m app.scripts.assign_annotations adjudicate --batch adjud1 --seed 2026   # then export + import again

`add` creates one annotator account per name with a pseudonym REV-01, REV-02, ...; the
database stores only the pseudonym. The name-to-pseudonym list goes to
data/annotation/packs/reviewers.csv, which is git-ignored, so names never reach the
repository or any report. `selection` writes the 600 selected drafts' ids (current
prompt version) for the planner. `export` writes one pack per reviewer with their
unfinished assignments. `import` stores a returned CSV as labels with the same rules as
the online tool (labels are final; label or skip, not both) and reports quick answers.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import secrets
import statistics
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, Label, User
from app.routers.annotate import RUBRIC_VERSION, LabelIn

ROOT = Path(__file__).resolve().parents[3]
PACKS = ROOT / "data" / "annotation" / "packs"
TEMPLATE = Path(__file__).with_name("review_pack_template.html")
SELECTION_DRAFTS = ROOT / "data" / "annotation" / "selection_v1_drafts.txt"
QUICK_MS = 15_000  # under 15 s for a ticket, draft and evidence is too quick to be a real read


async def add(names: list[str]) -> list[tuple[str, str]]:
    created = []
    async with SessionLocal() as db:
        existing = await db.scalar(select(func.count()).select_from(Annotator).where(Annotator.pseudonym.like("REV-__")))
        for k, name in enumerate(names, start=(existing or 0) + 1):
            pseudonym = f"REV-{k:02d}"
            user = User(email=f"{pseudonym.lower()}@review.local", full_name=pseudonym, role="annotator",
                        hashed_password=hash_password(secrets.token_urlsafe(12)))
            db.add(user)
            await db.flush()
            db.add(Annotator(user_id=user.id, pseudonym=pseudonym))
            created.append((pseudonym, name))
        await db.commit()
    PACKS.mkdir(parents=True, exist_ok=True)
    path = PACKS / "reviewers.csv"
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["pseudonym", "name"])
        w.writerows(created)
    return created


async def selection(version: str = "v1") -> int:
    sys.path.insert(0, str(ROOT / "ai"))
    from generation.drafting import DRAFT_PROMPT_VERSION

    chosen = json.loads((ROOT / "data" / "annotation" / f"selection_{version}.json").read_text(encoding="utf-8"))
    ticket_ids = sorted({t for ids in chosen["selected"].values() for t in ids})
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(Draft.benchmark_ticket_id, Draft.id, Draft.created_at)
            .where(Draft.benchmark_version == version, Draft.prompt_version == DRAFT_PROMPT_VERSION,
                   Draft.benchmark_ticket_id.in_(ticket_ids))
        )).all()
    latest: dict[str, tuple] = {}
    for tid, did, created in rows:
        if tid not in latest or created > latest[tid][1]:
            latest[tid] = (did, created)
    missing = [t for t in ticket_ids if t not in latest]
    if missing:
        raise SystemExit(f"{len(missing)} selected tickets have no {DRAFT_PROMPT_VERSION} draft, e.g. {missing[0]}")
    SELECTION_DRAFTS.write_text("".join(f"{latest[t][0]}\n" for t in ticket_ids), encoding="utf-8")
    return len(ticket_ids)


async def export() -> list[Path]:
    template = TEMPLATE.read_text(encoding="utf-8")
    PACKS.mkdir(parents=True, exist_ok=True)
    written = []
    async with SessionLocal() as db:
        annotators = list(await db.scalars(
            select(Annotator).join(User, User.id == Annotator.user_id)
            .where(Annotator.active.is_(True), ~User.email.endswith("@demo.local")).order_by(Annotator.pseudonym)
        ))
        for annotator in annotators:
            rows = (await db.execute(
                select(AnnotationAssignment, Draft, BenchmarkTicket)
                .join(Draft, Draft.id == AnnotationAssignment.draft_id)
                .join(BenchmarkTicket, (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                      & (BenchmarkTicket.benchmark_version == Draft.benchmark_version))
                .where(AnnotationAssignment.annotator_id == annotator.id, AnnotationAssignment.completed_at.is_(None))
                .order_by(AnnotationAssignment.position)
            )).all()
            if not rows:
                continue
            pack = {
                "pack_id": uuid.uuid4().hex[:8], "pseudonym": annotator.pseudonym, "rubric_version": RUBRIC_VERSION,
                "items": [{
                    "assignment_id": str(a.id),
                    "ticket": {"subject": t.subject, "body": t.body, "attachment_text": t.attachment_text},
                    "draft": {"can_answer": d.can_answer,
                              "steps": [{"text": s.get("text", ""), "citations": s.get("citations", [])} for s in d.steps],
                              "missing_information": d.missing_information},
                    "evidence": [{"n": e.get("n"), "title": e.get("title"), "text": e.get("text")} for e in d.evidence],
                } for a, d, t in rows],
            }
            html = template.replace("__PACK__", json.dumps(pack, ensure_ascii=False).replace("</", "<\\/"))
            out = PACKS / f"review_pack_{annotator.pseudonym}.html"
            out.write_text(html, encoding="utf-8")
            for a, _, _ in rows:
                a.served_at = a.served_at or datetime.now(timezone.utc)
            written.append(out)
        await db.commit()
    return written


async def import_csv(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    report = {"file": path.name, "rows": len(rows), "stored": 0, "already_labelled": 0, "errors": [], "quick": 0}
    times = []
    async with SessionLocal() as db:
        for n, row in enumerate(rows, start=2):
            try:
                body = LabelIn(label=row["label"] or None,
                               reason_codes=[c for c in row["reason_codes"].split(";") if c],
                               note=row["note"] or None, skipped_reason=row["skipped_reason"] or None,
                               time_taken_ms=int(row["time_taken_ms"]))
            except (ValueError, KeyError) as exc:
                report["errors"].append(f"line {n}: {exc}".splitlines()[0])
                continue
            assignment = await db.get(AnnotationAssignment, uuid.UUID(row["assignment_id"]))
            annotator = await db.get(Annotator, assignment.annotator_id) if assignment else None
            if assignment is None or annotator is None or annotator.pseudonym != row["pseudonym"]:
                report["errors"].append(f"line {n}: assignment does not belong to {row['pseudonym']}")
                continue
            if assignment.completed_at is not None:
                report["already_labelled"] += 1
                continue
            db.add(Label(assignment_id=assignment.id, label=body.label, reason_codes=list(body.reason_codes),
                         note=body.note, skipped_reason=body.skipped_reason, time_taken_ms=body.time_taken_ms,
                         rubric_version=RUBRIC_VERSION))
            assignment.completed_at = datetime.now(timezone.utc)
            report["stored"] += 1
            times.append(body.time_taken_ms)
            report["quick"] += body.time_taken_ms < QUICK_MS
        if report["errors"]:
            await db.rollback()  # all or nothing: fix the file and import again
            report["stored"] = 0
        else:
            await db.commit()
    report["median_seconds"] = round(statistics.median(times) / 1000, 1) if times else None
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add").add_argument("--names", nargs="+", required=True)
    sub.add_parser("selection")
    sub.add_parser("export")
    sub.add_parser("import").add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    if args.cmd == "add":
        for pseudonym, name in asyncio.run(add(args.names)):
            print(f"{pseudonym}  {name}")
        print(f"name list: {(PACKS / 'reviewers.csv').relative_to(ROOT)} (git-ignored)")
    elif args.cmd == "selection":
        print(f"{asyncio.run(selection())} draft ids -> {SELECTION_DRAFTS.relative_to(ROOT)}")
    elif args.cmd == "export":
        for out in asyncio.run(export()):
            print(out.relative_to(ROOT))
    else:
        for f in args.files:
            r = asyncio.run(import_csv(f))
            flag = f"  WARNING: {r['quick']} answers under {QUICK_MS // 1000} s" if r["quick"] else ""
            print(f"{r['file']}: {r['stored']} stored, {r['already_labelled']} already labelled, "
                  f"median {r['median_seconds']} s{flag}")
            for e in r["errors"]:
                print("  error:", e)


if __name__ == "__main__":
    main()

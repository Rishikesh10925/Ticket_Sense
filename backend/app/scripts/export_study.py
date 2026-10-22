"""Export the user-study results and the blind grading sheet (Roadmap Week 11).

    python -m app.scripts.export_study

Writes to data/study/:

    tasks.csv           one row per submitted task: participant code, set, condition,
                        lane, action, handling time
    grading_sheet.csv   every written reply, shuffled, with the ticket text and empty
                        `grade` (A/M/R/W, labelling rubric) and `note` columns; no
                        participant, condition or lane, so grading is blind
    grading_key.csv     grade_id -> task, kept apart from the sheet until grading is done

Escalations have no reply and are not graded; they appear in tasks.csv only.
"""

from __future__ import annotations

import asyncio
import csv
import random
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import BenchmarkTicket, StudyParticipant, StudyTask

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "study"
SEED = 2026


async def main() -> None:
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(StudyTask, StudyParticipant.code, BenchmarkTicket.subject, BenchmarkTicket.body)
            .join(StudyParticipant, StudyParticipant.id == StudyTask.participant_id)
            .join(BenchmarkTicket, (BenchmarkTicket.id == StudyTask.benchmark_ticket_id)
                  & (BenchmarkTicket.benchmark_version == "v1"))
            .where(StudyTask.submitted_at.is_not(None))
            .order_by(StudyParticipant.code, StudyTask.position)
        )).all()
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "tasks.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "participant", "position", "ticket_id", "set", "condition", "lane", "action", "time_ms"])
        for t, code, _, _ in rows:
            w.writerow([t.id, code, t.position, t.benchmark_ticket_id, t.ticket_set, t.condition, t.lane, t.action,
                        t.time_ms])

    graded = [(t, subject, body) for t, _, subject, body in rows if t.final_reply]
    random.Random(SEED).shuffle(graded)
    with open(OUT / "grading_sheet.csv", "w", encoding="utf-8", newline="") as sheet, \
            open(OUT / "grading_key.csv", "w", encoding="utf-8", newline="") as key:
        ws, wk = csv.writer(sheet), csv.writer(key)
        ws.writerow(["grade_id", "ticket_subject", "ticket_body", "reply", "grade", "note"])
        wk.writerow(["grade_id", "task_id"])
        for i, (t, subject, body) in enumerate(graded, start=1):
            gid = f"G{i:03d}"
            ws.writerow([gid, subject, body, t.final_reply, "", ""])
            wk.writerow([gid, t.id])
    print(f"{len(rows)} submitted tasks, {len(graded)} replies to grade -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())

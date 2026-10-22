"""Create user-study participants and their 40 tasks (Roadmap Week 11; docs/study/user-study/README.md).

    python -m app.scripts.setup_study --participants 8

Adds participants P01, P02, ... up to the number given (existing ones are kept). Each
gets a `participant` account `p01@study.local` with a random password, printed once,
and 40 tasks: set A in their first condition, then set B in the other. Conditions
alternate by sign-up order. Each ticket's lane, score and reasons are computed once with
the active gate thresholds and are the same for everyone. The manifest (codes and
orders, no passwords) is written to data/study/participants.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
from pathlib import Path

from sqlalchemy import func, select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import BenchmarkTicket, Draft, GateThresholds, SignalVector, StudyParticipant, StudyTask, User
from app.services.study import fixed_lane, order_for, plan

ROOT = Path(__file__).resolve().parents[3]
SETS = ROOT / "docs" / "study" / "user-study" / "ticket-sets.json"
MANIFEST = ROOT / "data" / "study" / "participants.json"


async def _thresholds(db):
    from gate.service import Thresholds

    active = await db.scalar(select(GateThresholds).where(GateThresholds.active.is_(True)))
    if active is None:
        return None, None
    guard = (active.calibration or {}).get("guard") or {}
    return Thresholds(active.version, active.fast_threshold, active.assisted_threshold,
                      guard.get("min_dept_prob"), guard.get("min_probe_margin")), active.version


async def _stimuli(db, ticket_ids: list[str]) -> dict[str, dict]:
    """The current draft and its fixed lane for every study ticket."""
    from generation.drafting import DRAFT_PROMPT_VERSION

    thresholds, version = await _thresholds(db)
    out = {}
    for tid in ticket_ids:
        draft = await db.scalar(
            select(Draft).where(Draft.benchmark_ticket_id == tid, Draft.benchmark_version == "v1",
                                Draft.prompt_version == DRAFT_PROMPT_VERSION)
            .order_by(Draft.created_at.desc()).limit(1)
        )
        if draft is None:
            raise SystemExit(f"no {DRAFT_PROMPT_VERSION} draft for study ticket {tid}")
        ticket = await db.get(BenchmarkTicket, (tid, "v1"))
        vector = await db.scalar(
            select(SignalVector).where(SignalVector.draft_id == draft.id, SignalVector.feature_version == "features-v1")
        )
        lane, score, reasons = fixed_lane(draft, dict(vector.features) if vector else {}, ticket.department, thresholds)
        out[tid] = {"draft_id": draft.id, "lane": lane, "score": score, "reasons": reasons}
    print(f"lanes with thresholds {version}: "
          + ", ".join(f"{k} {sum(v['lane'] == k for v in out.values())}" for k in ("fast", "assisted", "escalate")))
    return out


async def main(n: int) -> None:
    sets = json.loads(SETS.read_text(encoding="utf-8"))
    set_a = [t["ticket_id"] for t in sets["set_a"]]
    set_b = [t["ticket_id"] for t in sets["set_b"]]
    async with SessionLocal() as db:
        existing = await db.scalar(select(func.count()).select_from(StudyParticipant)) or 0
        stimuli = await _stimuli(db, set_a + set_b) if existing < n else {}
        for index in range(existing, n):
            code = f"P{index + 1:02d}"
            order = order_for(index)
            password = secrets.token_urlsafe(9)
            user = User(email=f"{code.lower()}@study.local", full_name=f"Participant {code}", role="participant",
                        hashed_password=hash_password(password))
            db.add(user)
            await db.flush()
            participant = StudyParticipant(user_id=user.id, code=code, order=order)
            db.add(participant)
            await db.flush()
            for position, (tid, ticket_set, condition) in enumerate(plan(code, order, set_a, set_b)):
                s = stimuli[tid]
                db.add(StudyTask(participant_id=participant.id, draft_id=s["draft_id"], benchmark_ticket_id=tid,
                                 ticket_set=ticket_set, condition=condition, position=position, lane=s["lane"],
                                 score=s["score"], reasons=s["reasons"]))
            print(f"created {code} ({order}): {user.email}  password {password}")
        await db.commit()
        rows = (await db.execute(select(StudyParticipant.code, StudyParticipant.order).order_by(StudyParticipant.code))).all()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"participants": [{"code": c, "order": o} for c, o in rows]}, indent=1) + "\n",
                        encoding="utf-8")
    print(f"{len(rows)} participants -> {MANIFEST.relative_to(ROOT)}. Passwords are shown only once.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--participants", type=int, default=8)
    asyncio.run(main(parser.parse_args().participants))

"""Load certified lane thresholds from a training report and make them active
(Roadmap Week 8: "gate service reading versioned thresholds from the database").

    python -m app.scripts.load_thresholds --report docs/results/confidence-v1-judge.json --version t-judge-1
    python -m app.scripts.load_thresholds --report docs/results/confidence-v1-judge.json --guard docs/results/shift-v1-judge.json --version t-judge-2

The previous active set is deactivated, never deleted, so old decisions stay explainable.
"""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import update

from app.database import SessionLocal
from app.models.gate import GateThresholds

ROOT = Path(__file__).resolve().parents[3]


async def load(report_path: Path, version: str, guard_path: Path | None = None) -> GateThresholds:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    guard = json.loads(guard_path.read_text(encoding="utf-8"))["guard"] if guard_path else {}
    t = report["thresholds"]
    async with SessionLocal() as db:
        await db.execute(update(GateThresholds).where(GateThresholds.active.is_(True)).values(active=False))
        row = GateThresholds(
            version=version,
            model_version=f"{report['model_version']}-{report['labels']}",
            label_source=report["labels"],
            alpha_fast=0.10,
            alpha_assisted=0.40,
            delta=0.10,
            fast_threshold=t["fast"]["threshold"],
            assisted_threshold=t["assisted"]["threshold"],
            calibration={"report": report_path.name, "n": report["n"], "thresholds": t, "status": report["status"],
                         "alpha_curve": report.get("alpha_curve", []),
                         # Shift guard from the unseen-topic experiment (ai/confidence_model/shift.py).
                         "guard": guard, "guard_report": guard_path.name if guard_path else None},
            active=True,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Activate a certified threshold set")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--guard", type=Path, default=None, help="shift report whose guard to activate")
    args = parser.parse_args()
    def resolve(p: Path | None) -> Path | None:
        return None if p is None else (p if p.is_absolute() else ROOT / p)

    row = asyncio.run(load(resolve(args.report), args.version, resolve(args.guard)))
    print(f"active: {row.version} fast={row.fast_threshold} assisted={row.assisted_threshold} "
          f"guard={row.calibration.get('guard') or 'off'} ({row.label_source})")


if __name__ == "__main__":
    main()

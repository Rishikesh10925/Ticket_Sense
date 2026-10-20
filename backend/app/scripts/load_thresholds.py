"""Load certified lane thresholds from a training report and make them active
(Roadmap Week 8: "gate service reading versioned thresholds from the database").

    python -m app.scripts.load_thresholds --report docs/results/confidence-v1-judge.json --version t-judge-1

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


async def load(report_path: Path, version: str) -> GateThresholds:
    report = json.loads(report_path.read_text(encoding="utf-8"))
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
                         "alpha_curve": report.get("alpha_curve", [])},
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
    args = parser.parse_args()
    row = asyncio.run(load(ROOT / args.report if not args.report.is_absolute() else args.report, args.version))
    print(f"active: {row.version} fast={row.fast_threshold} assisted={row.assisted_threshold} ({row.label_source})")


if __name__ == "__main__":
    main()

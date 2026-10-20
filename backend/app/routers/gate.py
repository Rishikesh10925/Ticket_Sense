"""Admin view of the confidence gate's error budget (Blueprint V2 §13.4; Roadmap Week 8):
the active certified thresholds, the coverage each error budget would allow, and the
history of threshold sets. Read-only: thresholds change only by certifying a new set
(app/scripts/load_thresholds.py), never by editing a number in the UI."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import GateThresholds, User

router = APIRouter(prefix="/gate", tags=["gate"])


def _out(t: GateThresholds) -> dict:
    return {
        "version": t.version,
        "model_version": t.model_version,
        "label_source": t.label_source,
        "alpha_fast": t.alpha_fast,
        "alpha_assisted": t.alpha_assisted,
        "delta": t.delta,
        "fast_threshold": t.fast_threshold,
        "assisted_threshold": t.assisted_threshold,
        "active": t.active,
        "created_at": t.created_at.isoformat(),
    }


@router.get("/thresholds")
async def get_thresholds(
    current_user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)
) -> dict:
    sets = list(await db.scalars(select(GateThresholds).order_by(GateThresholds.created_at.desc())))
    active = next((t for t in sets if t.active), None)
    return {
        "active": _out(active) if active else None,
        "alpha_curve": (active.calibration or {}).get("alpha_curve", []) if active else [],
        "calibration_n": ((active.calibration or {}).get("n") or {}).get("calib") if active else None,
        "history": [_out(t) for t in sets],
    }

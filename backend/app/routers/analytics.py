"""Analytics aggregation for the Admin dashboard (Week 10).

Every number here is computed from real `tickets`/`feedback` rows — nothing here is
precomputed or cached, so it always reflects the current database state. See
docs/analytics-api.md for the exact definitions (especially "escalation rate" and
"agreement rate", both of which have a specific, non-obvious denominator) and why real
and synthetic feedback are reported separately rather than blended.
"""

import sys
from collections import Counter
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import Department, Feedback, Ticket, User
from app.schemas.analytics import (
    AnalyticsSummary,
    CalibrationBucket,
    ConfidenceBucket,
    ConfidenceModelReport,
    DailyTrendPoint,
    DepartmentBreakdown,
    FeedbackSourceSummary,
    ReviewActionCounts,
    ReviewerBreakdown,
)

# app/routers/analytics.py -> repo_root/ai must be importable, to reuse the exact
# same label-derivation logic the confidence model retrains on (Week 9) — an
# "agreement rate" computed by different rules than the model's own success/failure
# labels would be a second, inconsistent definition of the same idea.
_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))
_AI_CONFIDENCE_DIR = _AI_DIR / "confidence"
if str(_AI_CONFIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_CONFIDENCE_DIR))

from labels import SYNTHETIC_REVIEWER_EMAIL, label_from_feedback  # noqa: E402

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _bucket_label(score: float) -> str:
    floor = min(int(score * 10) * 10, 90)  # score==1.0 falls in the 90-100% bucket, not a new 100-110% one
    return f"{floor}-{floor + 10}%"


def _feedback_summary(rows: list[tuple[Feedback, Ticket]]) -> FeedbackSourceSummary:
    actions = Counter(feedback.action for feedback, _ in rows)
    labels = [
        label_from_feedback(feedback.action, ticket.ai_draft_reply, feedback.edited_reply)
        for feedback, ticket in rows
    ]
    decided = [label for label in labels if label is not None]
    agreement_rate = (sum(decided) / len(decided)) if decided else None

    return FeedbackSourceSummary(
        total=len(rows),
        review_actions=ReviewActionCounts(
            accept=actions.get("accept", 0),
            edit=actions.get("edit", 0),
            reject=actions.get("reject", 0),
            escalate=actions.get("escalate", 0),
            doubt=actions.get("doubt", 0),
            resolve=actions.get("resolve", 0),
        ),
        agreement_rate=agreement_rate,
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    current_user: User = Depends(require_role("admin", "department_engineer")),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    """Admin sees everything. A department_engineer can call this too (their own
    resolved/rejected/escalated/in_review numbers, for their own dashboard), but the
    system-wide and by_department/by_reviewer breakdowns aren't department-scoped
    for them here — that's fine, since none of it is sensitive (every number is
    already an aggregate, not tied to a specific customer or ticket), but by_reviewer
    is narrowed to just their own row below so they don't see other engineers'
    individual performance."""
    all_tickets = list(await db.scalars(select(Ticket)))
    by_status = dict(Counter(t.status for t in all_tickets))

    scored = [t for t in all_tickets if t.confidence_score is not None]
    escalated_count = sum(1 for t in scored if t.status == "escalated")
    escalation_rate = (escalated_count / len(scored)) if scored else None

    bucket_counts = Counter(_bucket_label(t.confidence_score) for t in scored)
    confidence_distribution = []
    for floor in range(0, 100, 10):
        label = f"{floor}-{floor + 10}%"
        confidence_distribution.append(ConfidenceBucket(label=label, count=bucket_counts.get(label, 0)))

    departments = list(await db.scalars(select(Department).order_by(Department.name)))
    tickets_by_dept: dict[UUID, list[Ticket]] = {d.id: [] for d in departments}
    for t in all_tickets:
        if t.department_id in tickets_by_dept:
            tickets_by_dept[t.department_id].append(t)

    by_department = []
    for dept in departments:
        dept_tickets = tickets_by_dept[dept.id]
        dept_scored = [t for t in dept_tickets if t.confidence_score is not None]
        dept_escalated = sum(1 for t in dept_scored if t.status == "escalated")
        by_department.append(
            DepartmentBreakdown(
                department_id=dept.id,
                department_name=dept.name,
                total_tickets=len(dept_tickets),
                scored_tickets=len(dept_scored),
                escalation_rate=(dept_escalated / len(dept_scored)) if dept_scored else None,
                avg_confidence=(sum(t.confidence_score for t in dept_scored) / len(dept_scored))
                if dept_scored
                else None,
            )
        )

    feedback_rows = (
        await db.execute(
            select(Feedback, Ticket, User)
            .join(Ticket, Feedback.ticket_id == Ticket.id)
            .join(User, Feedback.reviewer_id == User.id)
        )
    ).all()
    real_rows = [(f, t) for f, t, reviewer in feedback_rows if reviewer.email != SYNTHETIC_REVIEWER_EMAIL]
    synthetic_rows = [(f, t) for f, t, reviewer in feedback_rows if reviewer.email == SYNTHETIC_REVIEWER_EMAIL]

    # Per-engineer breakdown — excludes the synthetic-reviewer placeholder (it isn't
    # a real engineer). `in_review` is the engineer's department queue count, not a
    # per-reviewer figure: a ticket has no assigned reviewer until someone acts on
    # it, so "how many are waiting" is only meaningful at the department level.
    engineers = list(
        await db.scalars(
            select(User).where(User.role == "department_engineer", User.email != SYNTHETIC_REVIEWER_EMAIL)
        )
    )
    dept_name_by_id = {d.id: d.name for d in departments}
    in_review_by_dept = {
        dept_id: sum(1 for t in dept_tickets if t.status == "drafted")
        for dept_id, dept_tickets in tickets_by_dept.items()
    }
    actions_by_reviewer: dict[UUID, Counter] = {}
    for feedback, _ in real_rows:
        actions_by_reviewer.setdefault(feedback.reviewer_id, Counter())[feedback.action] += 1

    by_reviewer = [
        ReviewerBreakdown(
            reviewer_id=engineer.id,
            reviewer_name=engineer.full_name,
            reviewer_email=engineer.email,
            department_name=dept_name_by_id.get(engineer.department_id, "—"),
            resolved=actions_by_reviewer.get(engineer.id, Counter()).get("accept", 0)
            + actions_by_reviewer.get(engineer.id, Counter()).get("edit", 0)
            + actions_by_reviewer.get(engineer.id, Counter()).get("resolve", 0),
            rejected=actions_by_reviewer.get(engineer.id, Counter()).get("reject", 0),
            escalated=actions_by_reviewer.get(engineer.id, Counter()).get("escalate", 0)
            + actions_by_reviewer.get(engineer.id, Counter()).get("doubt", 0),
            in_review=in_review_by_dept.get(engineer.department_id, 0),
        )
        for engineer in engineers
    ]

    if current_user.role == "department_engineer":
        by_reviewer = [row for row in by_reviewer if row.reviewer_id == current_user.id]

    return AnalyticsSummary(
        total_tickets=len(all_tickets),
        by_status=by_status,
        scored_tickets=len(scored),
        escalation_rate=escalation_rate,
        confidence_distribution=confidence_distribution,
        by_department=by_department,
        by_reviewer=by_reviewer,
        real_feedback=_feedback_summary(real_rows),
        synthetic_feedback=_feedback_summary(synthetic_rows),
    )


@router.get("/confidence-model", response_model=ConfidenceModelReport)
async def get_confidence_model_report(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> ConfidenceModelReport:
    """How well the confidence score actually predicts human agreement — a
    reliability diagram (calibration) plus a day-by-day trend, both built from
    every Feedback row with a resolvable label (see labels.label_from_feedback)
    on a ticket that was actually scored. Real and synthetic bootstrap feedback are
    pooled here (unlike /summary's real_feedback/synthetic_feedback split) because
    calibration is a property of the model's whole training signal, not of who
    provided it — total_labeled's real/synthetic breakdown is reported alongside so
    the split is still visible, not hidden."""
    rows = (
        await db.execute(
            select(Feedback, Ticket, User)
            .join(Ticket, Feedback.ticket_id == Ticket.id)
            .join(User, Feedback.reviewer_id == User.id)
            .where(Ticket.confidence_score.isnot(None))
        )
    ).all()

    labeled: list[tuple[float, bool, object, bool]] = []  # (score, label, created_at, is_synthetic)
    for feedback, ticket, reviewer in rows:
        label = label_from_feedback(feedback.action, ticket.ai_draft_reply, feedback.edited_reply)
        if label is None:
            continue
        labeled.append((ticket.confidence_score, label, ticket.created_at, reviewer.email == SYNTHETIC_REVIEWER_EMAIL))

    real_labeled = sum(1 for _, _, _, synthetic in labeled if not synthetic)
    synthetic_labeled = len(labeled) - real_labeled
    overall_agreement = (sum(1 for _, label, _, _ in labeled if label) / len(labeled)) if labeled else None

    buckets: dict[int, list[tuple[float, bool]]] = {}
    for score, label, _, _ in labeled:
        floor = min(int(score * 10) * 10, 90)
        buckets.setdefault(floor, []).append((score, label))

    calibration = []
    for floor in range(0, 100, 10):
        items = buckets.get(floor, [])
        count = len(items)
        avg_predicted = (sum(s for s, _ in items) / count) if count else None
        agreement = (sum(1 for _, label in items if label) / count) if count else None
        calibration.append(
            CalibrationBucket(
                label=f"{floor}-{floor + 10}%",
                avg_predicted_confidence=avg_predicted,
                actual_agreement_rate=agreement,
                count=count,
            )
        )

    by_day: dict[str, list[tuple[float, bool]]] = {}
    for score, label, created_at, _ in labeled:
        day = created_at.date().isoformat()
        by_day.setdefault(day, []).append((score, label))

    daily_trend = [
        DailyTrendPoint(
            date=day,
            avg_confidence=sum(s for s, _ in items) / len(items),
            agreement_rate=sum(1 for _, label in items if label) / len(items),
            count=len(items),
        )
        for day, items in sorted(by_day.items())
    ]

    return ConfidenceModelReport(
        total_labeled=len(labeled),
        real_labeled=real_labeled,
        synthetic_labeled=synthetic_labeled,
        overall_agreement_rate=overall_agreement,
        calibration=calibration,
        daily_trend=daily_trend,
    )

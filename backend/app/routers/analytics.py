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
    ConfidenceBucket,
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
        ),
        agreement_rate=agreement_rate,
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
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
            + actions_by_reviewer.get(engineer.id, Counter()).get("edit", 0),
            rejected=actions_by_reviewer.get(engineer.id, Counter()).get("reject", 0),
            escalated=actions_by_reviewer.get(engineer.id, Counter()).get("escalate", 0),
            in_review=in_review_by_dept.get(engineer.department_id, 0),
        )
        for engineer in engineers
    ]

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

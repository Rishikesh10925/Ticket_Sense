from uuid import UUID

from pydantic import BaseModel


class ReviewActionCounts(BaseModel):
    accept: int = 0
    edit: int = 0
    reject: int = 0
    escalate: int = 0


class ConfidenceBucket(BaseModel):
    # Half-open range [floor, floor + 10) as a percent, e.g. "70-80%".
    label: str
    count: int


class DepartmentBreakdown(BaseModel):
    department_id: UUID
    department_name: str
    total_tickets: int
    scored_tickets: int
    escalation_rate: float | None
    avg_confidence: float | None


class FeedbackSourceSummary(BaseModel):
    """One reviewer-feedback source's own summary — kept separate for real vs.
    synthetic (see ai/confidence/labels.py's SYNTHETIC_REVIEWER_EMAIL) rather than
    blended into one number, since synthetic bootstrap rows currently far outnumber
    real ones and a blended rate would be dominated by data nobody actually decided."""

    total: int
    review_actions: ReviewActionCounts
    agreement_rate: float | None  # fraction labeled "success" per labels.py::label_from_feedback


class ReviewerBreakdown(BaseModel):
    """One department_engineer's own record — excludes the synthetic-reviewer
    placeholder (see SYNTHETIC_REVIEWER_EMAIL), since that account isn't a real
    engineer and blending it in would misattribute bootstrap data to a person.
    `resolved` is accept + edit combined (both end a ticket at `reviewed`);
    `rejected`/`escalated` are that engineer's own reject/escalate actions.
    `in_review` is *not* per-reviewer data — it's the current `drafted` count for
    that engineer's department queue (shared by whoever reviews there), included
    here so the table reads as one complete row per engineer rather than requiring
    a second lookup against by_department."""

    reviewer_id: UUID
    reviewer_name: str
    reviewer_email: str
    department_name: str
    resolved: int
    rejected: int
    escalated: int
    in_review: int


class AnalyticsSummary(BaseModel):
    total_tickets: int
    by_status: dict[str, int]
    scored_tickets: int
    escalation_rate: float | None
    confidence_distribution: list[ConfidenceBucket]
    by_department: list[DepartmentBreakdown]
    by_reviewer: list[ReviewerBreakdown]
    real_feedback: FeedbackSourceSummary
    synthetic_feedback: FeedbackSourceSummary

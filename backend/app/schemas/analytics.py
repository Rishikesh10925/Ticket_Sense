from uuid import UUID

from pydantic import BaseModel


class ReviewActionCounts(BaseModel):
    accept: int = 0
    edit: int = 0
    reject: int = 0
    escalate: int = 0
    doubt: int = 0
    resolve: int = 0


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
    `resolved` is accept + edit + resolve combined (all three end a ticket, whether
    it had a draft or not); `rejected` is reject; `escalated` is escalate + doubt
    combined (both send a ticket back without the engineer deciding it).
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


class CalibrationBucket(BaseModel):
    """One decile of predicted confidence, e.g. '70-80%', against what actually
    happened for tickets scored in that range — a standard reliability-diagram
    bucket. A well-calibrated model has actual_agreement_rate tracking close to
    the bucket's own range; count is 0 (both rates null) for a decile nothing has
    landed in yet."""

    label: str
    avg_predicted_confidence: float | None
    actual_agreement_rate: float | None
    count: int


class DailyTrendPoint(BaseModel):
    # ISO date (YYYY-MM-DD) — the day the ticket was scored (Ticket.created_at),
    # not the day it was reviewed, since scoring happens in the same pipeline run.
    date: str
    avg_confidence: float
    agreement_rate: float
    count: int


class ConfidenceModelReport(BaseModel):
    """The confidence model's own health, as distinct from AnalyticsSummary's
    ticket/engineer-operations view — built from every scored ticket with a
    feedback-derived label (see ai/confidence/labels.py::label_from_feedback),
    real and synthetic bootstrap combined, since both are what the model was
    actually trained and calibrated against."""

    total_labeled: int
    real_labeled: int
    synthetic_labeled: int
    overall_agreement_rate: float | None
    calibration: list[CalibrationBucket]
    daily_trend: list[DailyTrendPoint]

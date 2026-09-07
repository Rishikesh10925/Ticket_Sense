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


class AnalyticsSummary(BaseModel):
    total_tickets: int
    by_status: dict[str, int]
    scored_tickets: int
    escalation_rate: float | None
    confidence_distribution: list[ConfidenceBucket]
    by_department: list[DepartmentBreakdown]
    real_feedback: FeedbackSourceSummary
    synthetic_feedback: FeedbackSourceSummary

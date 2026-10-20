from datetime import datetime

from pydantic import BaseModel


class DecisionOut(BaseModel):
    """The confidence gate's decision for a ticket's latest draft (docs/api-contract.md)."""

    lane: str  # fast | assisted | escalate
    score: float | None
    reasons: list[str]
    model_version: str
    thresholds_version: str | None
    label_source: str | None  # "judge" marks provisional thresholds, "human" the real ones
    fast_threshold: float | None
    assisted_threshold: float | None
    created_at: datetime

from datetime import datetime

from pydantic import BaseModel


class DraftStepOut(BaseModel):
    text: str
    citations: list[int]


class DraftPassageOut(BaseModel):
    n: int
    article_key: str | None
    title: str
    text: str


class DraftClaimOut(BaseModel):
    step_index: int
    claim_index: int
    text: str
    cited: list[int]
    support: float | None


class DraftOut(BaseModel):
    """The structured draft for the reviewer workbench (Blueprint V2 §9.1).

    `shown` is false in the escalation lane: steps, claims and groundedness are then
    withheld and only the ranked evidence and the reason are returned."""

    shown: bool
    lane: str  # "draft" | "escalate" until the Week 9 three-lane gate
    steps: list[DraftStepOut]
    missing_information: list[str]
    evidence: list[DraftPassageOut]
    groundedness: float | None
    claims: list[DraftClaimOut]
    weakest: list[DraftClaimOut]
    model: str
    prompt_version: str
    created_at: datetime

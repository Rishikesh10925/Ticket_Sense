"""Blinded annotation endpoints for outside reviewers (docs/annotation-tool.md;
Blueprint V2 §11.6 and Appendix C.3).

A reviewer only ever receives the ticket text, the draft and the passages the draft was
given. Never the confidence score, lane, signals, model name, ticket type, gold article,
split or whether the item is in the overlap set.
"""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import AnnotationAssignment, Annotator, BenchmarkTicket, Draft, Label, User

router = APIRouter(prefix="/annotate", tags=["annotate"])

RUBRIC_VERSION = "v1"
REASON_CODES = Literal[
    "wrong_source", "outdated_source", "missing_step", "invented_step",
    "did_not_address_question", "tone", "formatting", "other",
]


class AnnotationItem(BaseModel):
    assignment_id: str
    progress: dict
    rubric_version: str
    ticket: dict
    draft: dict
    evidence: list[dict]


class LabelIn(BaseModel):
    label: Literal["A", "M", "R", "W"] | None = None
    reason_codes: list[REASON_CODES] = Field(default_factory=list)
    note: str | None = Field(default=None, max_length=2000)
    skipped_reason: str | None = Field(default=None, max_length=500)
    time_taken_ms: int = Field(ge=0, le=3_600_000)

    @model_validator(mode="after")
    def _label_or_skip(self):
        if (self.label is None) == (self.skipped_reason is None):
            raise ValueError("give either a label or a skipped_reason, not both")
        return self


async def _annotator(user: User, db: AsyncSession) -> Annotator:
    annotator = await db.scalar(select(Annotator).where(Annotator.user_id == user.id, Annotator.active))
    if annotator is None:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not an active annotator")
    return annotator


async def _progress(db: AsyncSession, annotator: Annotator) -> dict:
    total = await db.scalar(
        select(func.count()).select_from(AnnotationAssignment).where(AnnotationAssignment.annotator_id == annotator.id)
    )
    done = await db.scalar(
        select(func.count())
        .select_from(AnnotationAssignment)
        .where(AnnotationAssignment.annotator_id == annotator.id, AnnotationAssignment.completed_at.is_not(None))
    )
    return {"done": done or 0, "total": total or 0}


def _blinded(assignment: AnnotationAssignment, draft: Draft, ticket: BenchmarkTicket, progress: dict) -> AnnotationItem:
    return AnnotationItem(
        assignment_id=str(assignment.id),
        progress=progress,
        rubric_version=RUBRIC_VERSION,
        ticket={"subject": ticket.subject, "body": ticket.body, "attachment_text": ticket.attachment_text},
        draft={
            "can_answer": draft.can_answer,
            "steps": [{"text": s.get("text", ""), "citations": s.get("citations", [])} for s in draft.steps],
            "missing_information": draft.missing_information,
        },
        evidence=[{"n": e.get("n"), "title": e.get("title"), "text": e.get("text")} for e in draft.evidence],
    )


@router.get("/next", response_model=AnnotationItem | None)
async def next_item(
    current_user: User = Depends(require_role("annotator")), db: AsyncSession = Depends(get_db)
) -> AnnotationItem | None:
    annotator = await _annotator(current_user, db)
    assignment = await db.scalar(
        select(AnnotationAssignment)
        .where(AnnotationAssignment.annotator_id == annotator.id, AnnotationAssignment.completed_at.is_(None))
        .order_by(AnnotationAssignment.position)
        .limit(1)
    )
    if assignment is None:
        return None
    draft = await db.get(Draft, assignment.draft_id)
    ticket = await db.get(BenchmarkTicket, (draft.benchmark_ticket_id, draft.benchmark_version))
    if assignment.served_at is None:
        assignment.served_at = datetime.now(timezone.utc)
        await db.commit()
    return _blinded(assignment, draft, ticket, await _progress(db, annotator))


@router.post("/{assignment_id}", status_code=http_status.HTTP_201_CREATED)
async def submit_label(
    assignment_id: str,
    body: LabelIn,
    current_user: User = Depends(require_role("annotator")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    annotator = await _annotator(current_user, db)
    assignment = await db.get(AnnotationAssignment, assignment_id)
    if assignment is None or assignment.annotator_id != annotator.id:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    if assignment.completed_at is not None:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Already labelled; labels are final")
    db.add(
        Label(
            assignment_id=assignment.id,
            label=body.label,
            reason_codes=list(body.reason_codes),
            note=body.note,
            skipped_reason=body.skipped_reason,
            time_taken_ms=body.time_taken_ms,
            rubric_version=RUBRIC_VERSION,
        )
    )
    assignment.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True, "progress": await _progress(db, annotator)}

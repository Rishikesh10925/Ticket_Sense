"""User-study endpoints for participants (Roadmap Week 11; docs/study/user-study/README.md).

A participant only ever receives the current ticket and, in the workbench condition,
what an engineer would see for it: the lane, the reasons, and (unless the lane is
escalate) the draft with its evidence and weakest claims. Never the ticket type, set
key, gold article or any other participant's work. Handling time is measured on the
server: from when a task is first served to when it is submitted.
"""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import BenchmarkTicket, Draft, DraftClaim, KnowledgeBase, StudyParticipant, StudyTask, User
from app.services.study import ACTIONS, rank_articles, search_terms

router = APIRouter(prefix="/study", tags=["study"])


class StudyItem(BaseModel):
    task_id: str
    progress: dict
    section: int
    condition: Literal["manual", "workbench"]
    ticket: dict
    lane: str | None = None
    reasons: list[str] = Field(default_factory=list)
    draft: dict | None = None
    evidence: list[dict] = Field(default_factory=list)
    weakest_claims: list[dict] = Field(default_factory=list)


class StudySubmission(BaseModel):
    action: Literal["accept", "edit", "write", "escalate"]
    final_reply: str | None = Field(default=None, max_length=20_000)


class KBResult(BaseModel):
    article_key: str | None
    title: str
    content: str


async def _participant(user: User, db: AsyncSession) -> StudyParticipant:
    participant = await db.scalar(select(StudyParticipant).where(StudyParticipant.user_id == user.id))
    if participant is None:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not a study participant")
    return participant


async def _progress(db: AsyncSession, participant: StudyParticipant) -> dict:
    total = await db.scalar(select(func.count()).select_from(StudyTask).where(StudyTask.participant_id == participant.id))
    done = await db.scalar(
        select(func.count()).select_from(StudyTask)
        .where(StudyTask.participant_id == participant.id, StudyTask.submitted_at.is_not(None))
    )
    return {"done": done or 0, "total": total or 0}


async def _item(db: AsyncSession, task: StudyTask, progress: dict) -> StudyItem:
    draft = await db.get(Draft, task.draft_id)
    ticket = await db.get(BenchmarkTicket, (draft.benchmark_ticket_id, draft.benchmark_version))
    item = StudyItem(
        task_id=str(task.id), progress=progress, section=1 if task.position < progress["total"] // 2 else 2,
        condition=task.condition,  # type: ignore[arg-type]
        ticket={"subject": ticket.subject, "body": ticket.body, "attachment_text": ticket.attachment_text},
    )
    if task.condition == "manual":
        return item
    item.lane, item.reasons = task.lane, list(task.reasons)
    if task.lane == "escalate":
        return item  # an escalated ticket has no AI draft (Blueprint V2 §9.1)
    item.draft = {"steps": [{"text": s.get("text", ""), "citations": s.get("citations", [])} for s in draft.steps]}
    item.evidence = [{"n": e.get("n"), "title": e.get("title"), "text": e.get("text")} for e in draft.evidence]
    claims = await db.scalars(
        select(DraftClaim).where(DraftClaim.draft_id == draft.id, DraftClaim.support.is_not(None))
        .order_by(DraftClaim.support).limit(3)
    )
    item.weakest_claims = [{"step": c.step_index + 1, "text": c.text, "support": round(c.support, 2)} for c in claims]
    return item


@router.get("/next", response_model=StudyItem | None)
async def next_task(
    current_user: User = Depends(require_role("participant")), db: AsyncSession = Depends(get_db)
) -> StudyItem | None:
    participant = await _participant(current_user, db)
    task = await db.scalar(
        select(StudyTask)
        .where(StudyTask.participant_id == participant.id, StudyTask.submitted_at.is_(None))
        .order_by(StudyTask.position).limit(1)
    )
    if task is None:
        return None
    if task.served_at is None:
        task.served_at = datetime.now(timezone.utc)
        await db.commit()
    return await _item(db, task, await _progress(db, participant))


@router.post("/tasks/{task_id}", status_code=http_status.HTTP_201_CREATED)
async def submit_task(
    task_id: str,
    body: StudySubmission,
    current_user: User = Depends(require_role("participant")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    participant = await _participant(current_user, db)
    task = await db.get(StudyTask, task_id)
    if task is None or task.participant_id != participant.id:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.submitted_at is not None:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Already submitted")
    if task.served_at is None:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Task was never shown")
    if body.action not in ACTIONS[task.condition]:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"'{body.action}' is not available in the {task.condition} condition")
    if body.action in ("accept", "edit") and task.lane == "escalate":
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No draft to accept or edit")
    reply = (body.final_reply or "").strip()
    if body.action != "escalate" and not reply:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Write a reply or escalate")
    now = datetime.now(timezone.utc)
    task.submitted_at, task.action = now, body.action
    task.final_reply = reply or None
    task.time_ms = int((now - task.served_at).total_seconds() * 1000)
    await db.commit()
    return {"ok": True, "progress": await _progress(db, participant)}


@router.get("/kb", response_model=list[KBResult])
async def search_kb(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(require_role("participant")),
    db: AsyncSession = Depends(get_db),
) -> list[KBResult]:
    """Keyword search over the served knowledge base; the same tool in both conditions."""
    await _participant(current_user, db)
    terms = search_terms(q)
    if not terms:
        return []
    rows = (await db.execute(
        select(KnowledgeBase.article_key, KnowledgeBase.title, KnowledgeBase.content).where(KnowledgeBase.served)
    )).all()
    return [KBResult(article_key=k, title=t, content=c) for k, t, c in rank_articles([tuple(r) for r in rows], terms)]

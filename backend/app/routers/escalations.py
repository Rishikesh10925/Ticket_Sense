"""Admin approval queue for escalated tickets.

An escalated ticket (the confidence gate failed, or an engineer escalated/doubted a
drafted one) no longer lands directly in a department's shared engineer queue — it's
gated behind an admin decision first. This mirrors, at the human-review layer, the same
principle the confidence gate itself embodies: don't let something uncertain reach the
next stage unreviewed. See app/routers/tickets.py's `_visibility_filter` for the other
half of this — an engineer only sees an escalated ticket once it's been approved and
assigned to them specifically here.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.database import get_db
from app.dependencies import require_role
from app.models import Department, Escalation, Ticket, User
from app.schemas.escalations import EscalationApprove, EscalationOut, EscalationReject, PendingEscalationOut
from app.services.ticket_lifecycle import TicketStatus, transition

router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.get("/pending", response_model=list[PendingEscalationOut])
async def list_pending_escalations(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[PendingEscalationOut]:
    """Every escalation an admin hasn't approved or rejected yet, newest first. Only
    the *latest* escalation per ticket matters — a ticket doubted twice (doubt ->
    admin rejects -> somehow escalated again) would otherwise show stale rows for a
    ticket that's already moved on, so this keeps only each ticket's most recent one."""
    latest_per_ticket = (
        select(Escalation.ticket_id, func.max(Escalation.created_at).label("latest"))
        .group_by(Escalation.ticket_id)
        .subquery()
    )
    rows = (
        await db.execute(
            select(Escalation, Ticket, Department.name)
            .join(Ticket, Escalation.ticket_id == Ticket.id)
            .join(latest_per_ticket, Escalation.ticket_id == latest_per_ticket.c.ticket_id)
            .outerjoin(Department, Ticket.department_id == Department.id)
            .where(
                Escalation.created_at == latest_per_ticket.c.latest,
                Escalation.admin_decision.is_(None),
            )
            .order_by(Escalation.created_at.desc())
        )
    ).all()

    return [
        PendingEscalationOut(
            id=escalation.id,
            ticket_id=ticket.id,
            ticket_subject=ticket.subject,
            department_id=ticket.department_id,
            department_name=department_name,
            priority=ticket.priority,
            reason=escalation.reason,
            confidence_score=escalation.confidence_score,
            created_at=escalation.created_at,
        )
        for escalation, ticket, department_name in rows
    ]


async def _get_pending_escalation_or_404(escalation_id: uuid.UUID, db: AsyncSession) -> tuple[Escalation, Ticket]:
    escalation = await db.get(Escalation, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    if escalation.admin_decision is not None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"This escalation was already {escalation.admin_decision}",
        )
    ticket = await db.get(Ticket, escalation.ticket_id)
    if ticket is None or ticket.status != TicketStatus.ESCALATED:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="This ticket is no longer in an escalated state",
        )
    return escalation, ticket


@router.post("/{escalation_id}/approve", response_model=EscalationOut)
async def approve_escalation(
    escalation_id: uuid.UUID,
    body: EscalationApprove,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> Escalation:
    """Approves the escalation and assigns it to a specific department_engineer, who
    can then resolve it via POST /tickets/{id}/resolve-escalation. The ticket's own
    status stays `escalated` — approval doesn't change what stage the ticket is at,
    only who's now responsible for it (see app/routers/tickets.py's
    _visibility_filter, which is what actually puts it in that engineer's queue)."""
    escalation, ticket = await _get_pending_escalation_or_404(escalation_id, db)

    engineer = await db.get(User, body.engineer_id)
    if engineer is None or engineer.role != "department_engineer" or not engineer.is_active:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Not an active department engineer")
    if engineer.department_id != ticket.department_id:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="That engineer isn't in this ticket's department",
        )

    escalation.admin_decision = "approved"
    escalation.escalated_to = engineer.id
    escalation.resolved_at = func.now()

    await db.commit()
    await db.refresh(escalation)
    return escalation


@router.post("/{escalation_id}/reject", response_model=EscalationOut)
async def reject_escalation(
    escalation_id: uuid.UUID,
    body: EscalationReject,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> Escalation:
    """Admin decides this escalation doesn't need routing to an engineer at all
    (e.g. a duplicate, or something the customer needs to resolve on their own) —
    closes the ticket directly, with no response ever generated. Distinct from
    approving-then-an-engineer-rejecting: there's no draft here to reject, and no
    engineer is ever involved."""
    escalation, ticket = await _get_pending_escalation_or_404(escalation_id, db)

    escalation.admin_decision = "rejected"
    escalation.admin_note = body.note
    escalation.resolved_at = func.now()
    ticket.status = transition(TicketStatus(ticket.status), TicketStatus.CLOSED)

    await db.commit()
    await db.refresh(escalation)
    return escalation

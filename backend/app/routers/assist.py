"""Browser extension API (README "Future enhancements").

The extension submits tickets through the normal `POST /tickets`, then polls
`GET /assist/tickets/{id}`. The answer rule was chosen by the project owner on
2026-11-16:

- fast and assisted lanes: the cited draft is shown to the user in the extension, with a
  "verify this" warning in the assisted lane. The ticket still waits for an engineer in
  the web app, exactly as before; the engineer's reply replaces the draft once reviewed.
- escalate lane (or a ticket the pipeline could not route): no draft. The extension opens
  the complaint portal registered for the department, fills the form, and the user
  clicks Submit. The extension never submits a form by itself.

This relaxes the web app's "end users never see drafts" rule for the extension only; the
web app's ticket endpoints are unchanged.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import ComplaintPortal, Department, Feedback, Ticket, User
from app.schemas.assist import AssistOut, AssistPortal, AssistSource, PortalIn, PortalOut, PortalReferenceIn
from app.services.ticket_lifecycle import TicketStatus

router = APIRouter(prefix="/assist", tags=["assist"])
portals_router = APIRouter(prefix="/portals", tags=["portals"])

ANSWER_LANES = ("fast", "assisted")
PROCESSING = (TicketStatus.SUBMITTED, TicketStatus.CLASSIFIED, TicketStatus.ROUTED)


async def _own_ticket(ticket_id: uuid.UUID, user: User, db: AsyncSession) -> Ticket:
    """Only the submitter (or an admin) can use a ticket through the extension."""
    if user.role not in ("end_user", "admin"):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail="The extension is for end users")
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if user.role == "end_user" and ticket.submitted_by != user.id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not permitted")
    return ticket


async def portal_for(db: AsyncSession, department_id: uuid.UUID | None) -> ComplaintPortal | None:
    """The department's active portal, else the active default portal."""
    if department_id is not None:
        portal = await db.scalar(select(ComplaintPortal).where(
            ComplaintPortal.department_id == department_id, ComplaintPortal.active.is_(True)))
        if portal is not None:
            return portal
    return await db.scalar(select(ComplaintPortal).where(
        ComplaintPortal.department_id.is_(None), ComplaintPortal.active.is_(True)))


async def _final_response(db: AsyncSession, ticket: Ticket) -> str | None:
    if ticket.status != TicketStatus.REVIEWED:
        return None
    feedback = await db.scalar(
        select(Feedback)
        .where(Feedback.ticket_id == ticket.id, Feedback.action.in_(("accept", "edit", "resolve")))
        .order_by(Feedback.created_at.desc())
        .limit(1)
    )
    if feedback is None:
        return None
    return ticket.ai_draft_reply if feedback.action == "accept" else feedback.edited_reply


def _portal_values(ticket: Ticket, user: User, department: Department | None) -> dict[str, str]:
    return {
        "subject": ticket.subject,
        "description": ticket.description,
        "category": department.name if department else "General",
        "priority": ticket.priority or "medium",
        "name": user.full_name,
        "email": user.email,
        "ticket_ref": f"TS-{str(ticket.id)[:8].upper()}",
    }


@router.get("/tickets/{ticket_id}", response_model=AssistOut)
async def assist_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssistOut:
    ticket = await _own_ticket(ticket_id, current_user, db)
    status = TicketStatus(ticket.status)
    out = AssistOut(ticket_id=ticket.id, status=ticket.status, lane=ticket.lane, state="processing",
                    message="TicketSense is reading your ticket and searching the knowledge base.",
                    portal_reference=ticket.portal_reference, portal_submitted_at=ticket.portal_submitted_at)
    if status in PROCESSING:
        return out

    if status == TicketStatus.REVIEWED:
        out.state = "resolved"
        out.final_response = await _final_response(db, ticket)
        out.message = "An engineer has answered your ticket."
        return out

    if status == TicketStatus.DRAFTED and ticket.lane in ANSWER_LANES and ticket.ai_draft_reply:
        out.state = "answer"
        out.answer = ticket.ai_draft_reply
        out.verify = ticket.lane == "assisted"
        out.sources = [AssistSource(title=c.get("title") or "Knowledge-base article")
                       for c in (ticket.ai_draft_citations or [])]
        out.message = ("Suggested answer from the knowledge base. An engineer has not checked it yet: "
                       "verify each step before you act on it." if out.verify else
                       "Answer from the knowledge base, with its sources.")
    elif status == TicketStatus.CLOSED:
        out.state = "closed"
        out.message = "This ticket is closed."
    else:
        out.state = "portal"
        out.message = ("The knowledge base does not answer this ticket. File it with the complaint "
                       "portal: TicketSense fills the form and you review it and click Submit.")

    department = await db.get(Department, ticket.department_id) if ticket.department_id else None
    portal = await portal_for(db, ticket.department_id)
    if portal is not None:
        submitter = await db.get(User, ticket.submitted_by)
        out.portal = AssistPortal(id=portal.id, name=portal.name, url=portal.url, field_map=portal.field_map,
                                  reference_selector=portal.reference_selector,
                                  values=_portal_values(ticket, submitter or current_user, department))
    elif out.state == "portal":
        out.message = "The knowledge base does not answer this ticket, and no complaint portal is registered yet."
    return out


@router.post("/tickets/{ticket_id}/portal-reference", response_model=AssistOut)
async def record_portal_reference(
    ticket_id: uuid.UUID,
    body: PortalReferenceIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssistOut:
    """The extension reports the reference number the portal showed after the user submitted."""
    ticket = await _own_ticket(ticket_id, current_user, db)
    if body.portal_id is not None and await db.get(ComplaintPortal, body.portal_id) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Portal not found")
    ticket.portal_reference = body.reference
    ticket.portal_id = body.portal_id
    ticket.portal_submitted_at = datetime.now(UTC)
    await db.commit()
    return await assist_ticket(ticket_id, current_user, db)


def _portal_out(portal: ComplaintPortal, department: Department | None) -> PortalOut:
    return PortalOut(id=portal.id, department_id=portal.department_id,
                     department_name=department.name if department else None, name=portal.name, url=portal.url,
                     field_map=portal.field_map, reference_selector=portal.reference_selector,
                     active=portal.active, updated_at=portal.updated_at)


@portals_router.get("", response_model=list[PortalOut])
async def list_portals(
    _: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)
) -> list[PortalOut]:
    rows = (await db.execute(
        select(ComplaintPortal, Department)
        .outerjoin(Department, Department.id == ComplaintPortal.department_id)
        .order_by(Department.name.nulls_last())
    )).all()
    return [_portal_out(p, d) for p, d in rows]


@portals_router.put("", response_model=PortalOut)
async def upsert_portal(
    body: PortalIn, _: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)
) -> PortalOut:
    """Create or replace the portal for a department (or the default portal)."""
    department = None
    if body.department_id is not None:
        department = await db.get(Department, body.department_id)
        if department is None:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Department not found")
    clause = (ComplaintPortal.department_id == body.department_id if body.department_id
              else ComplaintPortal.department_id.is_(None))
    portal = await db.scalar(select(ComplaintPortal).where(clause))
    if portal is None:
        portal = ComplaintPortal(department_id=body.department_id)
        db.add(portal)
    portal.name, portal.url, portal.field_map = body.name, body.url, body.field_map
    portal.reference_selector, portal.active = body.reference_selector, body.active
    portal.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(portal)
    return _portal_out(portal, department)


@portals_router.delete("/{portal_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_portal(
    portal_id: uuid.UUID, _: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)
) -> None:
    portal = await db.get(ComplaintPortal, portal_id)
    if portal is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Portal not found")
    await db.delete(portal)
    await db.commit()

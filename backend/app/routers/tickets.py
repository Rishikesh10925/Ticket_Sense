import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from fastapi import status as http_status
from fastapi.responses import FileResponse
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Escalation, Feedback, Ticket, User
from app.schemas.escalations import EscalationOut
from app.schemas.evidence import EvidenceOut
from app.schemas.feedback import FeedbackCreate
from app.schemas.tickets import TicketOut, build_ticket_out
from app.services.pipeline import run_ticket_pipeline
from app.services.retrieval import get_evidence_for_ticket
from app.services.ticket_lifecycle import TicketStatus, transition

router = APIRouter(prefix="/tickets", tags=["tickets"])

_PRIORITY_RANK = case({"high": 3, "medium": 2, "low": 1}, value=Ticket.priority, else_=0)

_ATTACHMENT_TYPES = {
    "image/png": "image",
    "image/jpeg": "image",
    "application/pdf": "pdf",
    "text/plain": "log",
    "text/x-log": "log",
}


def _visibility_filter(current_user: User):
    """Each role sees a different slice of tickets — see docs/architecture.md."""
    if current_user.role == "admin":
        return None
    if current_user.role == "department_engineer":
        return Ticket.department_id == current_user.department_id
    return Ticket.submitted_by == current_user.id


@router.post("", response_model=TicketOut, status_code=http_status.HTTP_201_CREATED)
async def create_ticket(
    background_tasks: BackgroundTasks,
    subject: str = Form(..., min_length=1, max_length=255),
    description: str = Form(..., min_length=1),
    attachment: UploadFile | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketOut:
    attachment_path: str | None = None
    attachment_type: str | None = None

    if attachment is not None and attachment.filename:
        attachment_type = _ATTACHMENT_TYPES.get(attachment.content_type or "")
        if attachment_type is None:
            raise HTTPException(
                status_code=http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Attachment must be an image, PDF, or log/text file",
            )
        contents = await attachment.read()
        if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Attachment exceeds {settings.max_upload_size_mb}MB",
            )

        ticket_upload_dir = Path(settings.upload_dir) / str(uuid.uuid4())
        ticket_upload_dir.mkdir(parents=True, exist_ok=True)
        saved_path = ticket_upload_dir / attachment.filename
        saved_path.write_bytes(contents)
        attachment_path = str(saved_path)

    ticket = Ticket(
        submitted_by=current_user.id,
        subject=subject,
        description=description,
        attachment_path=attachment_path,
        attachment_type=attachment_type,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    background_tasks.add_task(run_ticket_pipeline, ticket.id)
    return build_ticket_out(ticket, current_user.role)


@router.get("", response_model=list[TicketOut])
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    department_id: uuid.UUID | None = None,
    sort: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TicketOut]:
    """The department-scoped ticket queue. A Department Engineer's own queue is just
    this endpoint scoped to their department (see _visibility_filter); Admin can view
    any single department's queue with `?department_id=`, since Admin otherwise sees
    every ticket. `?sort=priority` orders high -> medium -> low -> unclassified,
    matching the Engineer queue UI's "sortable by priority" requirement.
    """
    query = select(Ticket)

    visibility = _visibility_filter(current_user)
    if visibility is not None:
        query = query.where(visibility)
    if status is not None:
        query = query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if department_id is not None and current_user.role == "admin":
        query = query.where(Ticket.department_id == department_id)

    if sort == "priority":
        query = query.order_by(_PRIORITY_RANK.desc(), Ticket.created_at.desc())
    else:
        query = query.order_by(Ticket.created_at.desc())

    result = await db.scalars(query)
    return [build_ticket_out(t, current_user.role) for t in result]


async def _get_ticket_or_403(ticket_id: uuid.UUID, current_user: User, db: AsyncSession) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if current_user.role == "end_user" and ticket.submitted_by != current_user.id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not permitted")
    if (
        current_user.role == "department_engineer"
        and ticket.department_id != current_user.department_id
    ):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not permitted")

    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketOut:
    ticket = await _get_ticket_or_403(ticket_id, current_user, db)
    return build_ticket_out(ticket, current_user.role)


@router.get("/{ticket_id}/attachment")
async def get_ticket_attachment(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Streams the ticket's stored attachment back — same access check as viewing the
    ticket itself. media_type isn't set explicitly: FileResponse infers it from the
    saved filename's extension (preserved from upload, see create_ticket), which is
    more precise than the coarse image/pdf/log bucket attachment_type stores."""
    ticket = await _get_ticket_or_403(ticket_id, current_user, db)
    if ticket.attachment_path is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="No attachment on this ticket")

    attachment_path = Path(ticket.attachment_path)
    if not attachment_path.is_file():
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Attachment file not found")

    return FileResponse(attachment_path, filename=attachment_path.name)


@router.get("/{ticket_id}/evidence", response_model=list[EvidenceOut])
async def get_ticket_evidence(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieved evidence passages for this ticket — department-scoped at the query
    level (see ai/embeddings/retrieve.py), using the same access check as viewing the
    ticket itself. Empty list if the ticket hasn't been routed to a department yet."""
    ticket = await _get_ticket_or_403(ticket_id, current_user, db)
    return await get_evidence_for_ticket(db, ticket)


def _require_reviewer(current_user: User) -> None:
    if current_user.role not in ("department_engineer", "admin"):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only a department engineer or admin can review a ticket",
        )


@router.get("/{ticket_id}/escalation", response_model=EscalationOut)
async def get_ticket_escalation(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Escalation:
    """The escalation record for a ticket the confidence gate (or a reviewer) sent
    straight to a human — reviewer-only, same reasoning as hiding confidence_score
    from end_user (see app/schemas/tickets.py's build_ticket_out): the reason
    references the confidence score/threshold that triggered it, which is an AI
    judgment the end user never sees."""
    _require_reviewer(current_user)
    ticket = await _get_ticket_or_403(ticket_id, current_user, db)
    escalation = await db.scalar(
        select(Escalation).where(Escalation.ticket_id == ticket.id).order_by(Escalation.created_at.desc())
    )
    if escalation is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="This ticket has not been escalated")
    return escalation


@router.post("/{ticket_id}/feedback", response_model=TicketOut, status_code=http_status.HTTP_201_CREATED)
async def submit_ticket_feedback(
    ticket_id: uuid.UUID,
    body: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketOut:
    """Records a reviewer's Accept/Edit/Reject/Escalate action on a drafted ticket —
    the primary training signal for confidence-model retraining going forward (see
    docs/confidence-labelling-guide.md). Only valid on a ticket currently `drafted`:
    there's nothing to review before that, and reviewing twice would silently
    overwrite the first reviewer's record. `edit`/`reject` intentionally leave
    `Ticket.ai_draft_reply` untouched — that's the AI's actual original output, an
    audit trail; the reviewer's edited text or rejection reason lives on the
    `Feedback` row instead, never overwriting what the AI produced.
    """
    _require_reviewer(current_user)
    ticket = await _get_ticket_or_403(ticket_id, current_user, db)

    if ticket.status != TicketStatus.DRAFTED:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Ticket must be 'drafted' to record reviewer feedback (currently '{ticket.status}')",
        )
    if body.action == "edit" and not body.edited_reply:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="edited_reply is required for the 'edit' action")
    if body.action == "reject" and not body.reject_reason:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="reject_reason is required for the 'reject' action")

    db.add(
        Feedback(
            ticket_id=ticket.id,
            reviewer_id=current_user.id,
            action=body.action,
            edited_reply=body.edited_reply,
            reject_reason=body.reject_reason,
        )
    )

    if body.action == "escalate":
        ticket.status = transition(TicketStatus(ticket.status), TicketStatus.ESCALATED)
        db.add(
            Escalation(
                ticket_id=ticket.id,
                reason="Engineer escalated after reviewing the draft",
                confidence_score=ticket.confidence_score,
            )
        )
    else:
        ticket.status = transition(TicketStatus(ticket.status), TicketStatus.REVIEWED)

    await db.commit()
    await db.refresh(ticket)
    return build_ticket_out(ticket, current_user.role)

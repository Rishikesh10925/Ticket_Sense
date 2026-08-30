import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Ticket, User
from app.schemas.evidence import EvidenceOut
from app.schemas.tickets import TicketOut
from app.services.classification import classify_and_route
from app.services.retrieval import get_evidence_for_ticket

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
) -> Ticket:
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

    background_tasks.add_task(classify_and_route, ticket.id)
    return ticket


@router.get("", response_model=list[TicketOut])
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    department_id: uuid.UUID | None = None,
    sort: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Ticket]:
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
    return list(result)


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
) -> Ticket:
    return await _get_ticket_or_403(ticket_id, current_user, db)


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

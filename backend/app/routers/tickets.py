import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Ticket, User
from app.schemas.tickets import TicketOut

router = APIRouter(prefix="/tickets", tags=["tickets"])

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
    return ticket


@router.get("", response_model=list[TicketOut])
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Ticket]:
    query = select(Ticket)

    visibility = _visibility_filter(current_user)
    if visibility is not None:
        query = query.where(visibility)
    if status is not None:
        query = query.where(Ticket.status == status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)

    query = query.order_by(Ticket.created_at.desc())
    result = await db.scalars(query)
    return list(result)


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ticket:
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

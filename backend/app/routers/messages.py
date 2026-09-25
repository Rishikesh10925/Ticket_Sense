"""Direct messaging between admin and department_engineer accounts.

Deliberately a two-party channel: an admin can message any engineer and vice versa,
but never a customer (end_user has no access to any endpoint here — see require_role
below), and not engineer-to-engineer or admin-to-admin either, since the only real
coordination need this closes is "admin needs to reach the engineer an escalation was
assigned to" and back.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import Department, Message, User
from app.schemas.messages import ChatContactOut, MessageCreate, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])

# The role a sender is allowed to message, keyed by the sender's own role.
_COUNTERPART_ROLE = {"admin": "department_engineer", "department_engineer": "admin"}

# The placeholder engineer account ai/confidence/synthetic_labels.py attributes
# bootstrap training feedback to (see labels.SYNTHETIC_REVIEWER_EMAIL) — not a real
# engineer, so it's excluded here the same way analytics.py excludes it from
# by_reviewer.
_SYNTHETIC_REVIEWER_EMAIL = "synthetic-reviewer@ticketsense.local"


@router.get("/contacts", response_model=list[ChatContactOut])
async def list_contacts(
    current_user: User = Depends(require_role("admin", "department_engineer")),
    db: AsyncSession = Depends(get_db),
) -> list[ChatContactOut]:
    """Every account on the other side of the admin/engineer divide, each annotated
    with that conversation's last message and unread count (both null/zero for a
    contact never messaged yet) — active conversations sort first, so the widget
    opens on what's actually waiting on you."""
    counterpart_role = _COUNTERPART_ROLE[current_user.role]
    contacts = list(
        await db.scalars(
            select(User)
            .where(User.role == counterpart_role, User.email != _SYNTHETIC_REVIEWER_EMAIL)
            .order_by(User.full_name)
        )
    )
    if not contacts:
        return []

    contact_ids = [c.id for c in contacts]
    all_messages = list(
        await db.scalars(
            select(Message)
            .where(
                or_(
                    (Message.sender_id == current_user.id) & (Message.recipient_id.in_(contact_ids)),
                    (Message.recipient_id == current_user.id) & (Message.sender_id.in_(contact_ids)),
                )
            )
            .order_by(Message.created_at.asc())
        )
    )

    departments = {d.id: d.name for d in await db.scalars(select(Department))}

    by_contact: dict[uuid.UUID, list[Message]] = {}
    for m in all_messages:
        other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        by_contact.setdefault(other_id, []).append(m)

    out = []
    for contact in contacts:
        thread = by_contact.get(contact.id, [])
        last = thread[-1] if thread else None
        unread = sum(1 for m in thread if m.recipient_id == current_user.id and m.read_at is None)
        out.append(
            ChatContactOut(
                user_id=contact.id,
                full_name=contact.full_name,
                role=contact.role,
                department_name=departments.get(contact.department_id) if contact.department_id else None,
                is_active=contact.is_active,
                last_message=last.body if last else None,
                last_message_at=last.created_at if last else None,
                unread_count=unread,
            )
        )

    out.sort(key=lambda c: (c.last_message_at is None, -c.last_message_at.timestamp() if c.last_message_at else 0))
    return out


@router.get("/thread/{other_user_id}", response_model=list[MessageOut])
async def get_thread(
    other_user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin", "department_engineer")),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    other = await db.get(User, other_user_id)
    if (
        other is None
        or other.role != _COUNTERPART_ROLE[current_user.role]
        or other.email == _SYNTHETIC_REVIEWER_EMAIL
    ):
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Contact not found")

    messages = list(
        await db.scalars(
            select(Message)
            .where(
                or_(
                    (Message.sender_id == current_user.id) & (Message.recipient_id == other_user_id),
                    (Message.sender_id == other_user_id) & (Message.recipient_id == current_user.id),
                )
            )
            .order_by(Message.created_at.asc())
        )
    )

    # Opening the thread is what marks the other side's messages read — same
    # "viewing it is acknowledging it" model as the rest of the app.
    unread = [m for m in messages if m.recipient_id == current_user.id and m.read_at is None]
    if unread:
        now = datetime.now(timezone.utc)
        for m in unread:
            m.read_at = now
        await db.commit()
        for m in messages:
            await db.refresh(m)

    return messages


@router.post("", response_model=MessageOut, status_code=http_status.HTTP_201_CREATED)
async def send_message(
    body: MessageCreate,
    current_user: User = Depends(require_role("admin", "department_engineer")),
    db: AsyncSession = Depends(get_db),
) -> Message:
    recipient = await db.get(User, body.recipient_id)
    if (
        recipient is None
        or recipient.role != _COUNTERPART_ROLE[current_user.role]
        or recipient.email == _SYNTHETIC_REVIEWER_EMAIL
    ):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Recipient must be a {_COUNTERPART_ROLE[current_user.role].replace('_', ' ')}",
        )
    if not body.body.strip():
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message can't be empty")

    message = Message(sender_id=current_user.id, recipient_id=recipient.id, body=body.body.strip())
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

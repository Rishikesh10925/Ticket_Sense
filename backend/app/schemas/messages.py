from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageCreate(BaseModel):
    recipient_id: UUID
    body: str


class MessageOut(BaseModel):
    id: UUID
    sender_id: UUID
    recipient_id: UUID
    body: str
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatContactOut(BaseModel):
    """One entry in the chat widget's contact list — the other staff account plus
    enough of the conversation's own state (last message, unread count) that the
    widget can render a thread list without a second request per contact."""

    user_id: UUID
    full_name: str
    role: str
    department_name: str | None
    is_active: bool
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int

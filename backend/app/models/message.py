import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Message(UUIDPKMixin, CreatedAtMixin, Base):
    """A direct message between two staff accounts. Deliberately admin<->engineer
    only — end_user customers never see or use this (enforced in
    app/routers/messages.py, not here, since role isn't on this table)."""

    __tablename__ = "messages"

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    # Set the first time the recipient loads a thread containing this message (see
    # GET /messages/{other_user_id}) — drives the unread badge in the chat widget.
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

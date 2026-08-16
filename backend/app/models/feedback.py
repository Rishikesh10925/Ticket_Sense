import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Feedback(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("action IN ('accept','edit','reject','escalate')", name="ck_feedback_action"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    edited_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)

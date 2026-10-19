import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Feedback(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "action IN ('accept','edit','reject','escalate','doubt','resolve')", name="ck_feedback_action"
        ),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    edited_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # Workbench (Week 7, migration 0020): structured reasons and decision time.
    reason_codes: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False, server_default="{}")
    time_taken_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)

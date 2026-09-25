import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Escalation(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "escalations"
    __table_args__ = (
        CheckConstraint("admin_decision IN ('approved','rejected')", name="ck_escalations_admin_decision"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    # Set once an admin approves this escalation and picks a specific engineer to
    # handle it (see app/routers/escalations.py) — the only thing that puts an
    # escalated ticket into a particular engineer's queue, since escalated tickets
    # are otherwise gated behind admin approval rather than visible department-wide.
    escalated_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Null while pending in the admin approval queue. 'approved' means escalated_to
    # is set and the assigned engineer now owns it; 'rejected' means the admin closed
    # it without routing it to anyone (admin_note explains why).
    admin_decision: Mapped[str | None] = mapped_column(Text(), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

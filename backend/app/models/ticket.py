import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Ticket(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("attachment_type IN ('image','pdf','log')", name="ck_tickets_attachment_type"),
        CheckConstraint("priority IN ('low','medium','high')", name="ck_tickets_priority"),
        CheckConstraint("sentiment IN ('positive','neutral','negative')", name="ck_tickets_sentiment"),
        CheckConstraint(
            "status IN ('submitted','classified','routed','drafted','reviewed','closed')",
            name="ck_tickets_status",
        ),
    )

    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    attachment_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attachment_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="submitted", index=True)
    ai_draft_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # [{"source_type": ..., "source_id": ..., "title": ...}, ...] — the evidence the
    # draft actually cited, in citation-number order. See docs/langgraph-pipeline.md.
    ai_draft_citations: Mapped[list | None] = mapped_column(JSONB(), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    confidence_features: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

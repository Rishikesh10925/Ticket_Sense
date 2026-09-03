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
    # Text pulled out of the attachment by ai/ocr/extract.py's extract node (OCR for
    # images, direct text-layer read for PDFs, plain read for logs) — see
    # docs/langgraph-pipeline.md. Null until the pipeline runs, and stays null if there
    # was no attachment at all.
    attachment_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # 0-1 for image attachments (EasyOCR's averaged per-detection confidence). Null for
    # PDF/log attachments (a direct text read isn't a probabilistic extraction, see
    # ai/ocr/extract.py's ExtractionResult) and for tickets with no attachment.
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="submitted", index=True)
    ai_draft_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # [{"source_type": ..., "source_id": ..., "title": ...}, ...] — the evidence the
    # draft actually cited, in citation-number order. See docs/langgraph-pipeline.md.
    ai_draft_citations: Mapped[list | None] = mapped_column(JSONB(), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    confidence_features: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)
    # Snapshot of the department's configured threshold at the moment this ticket was
    # scored — not a live reference to Department.confidence_threshold, which can
    # change later. Needed so a historical ticket's gate decision (Week 9) stays
    # explainable even after an admin adjusts the department's threshold. See
    # docs/confidence-model.md.
    confidence_threshold: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

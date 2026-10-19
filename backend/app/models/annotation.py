import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class Annotator(UUIDPKMixin, CreatedAtMixin, Base):
    """An outside reviewer (migration 0015). Exports and reports use `pseudonym` only."""

    __tablename__ = "annotators"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    pseudonym: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=true())


class AnnotationAssignment(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "annotation_assignments"
    __table_args__ = (
        UniqueConstraint("draft_id", "annotator_id", name="uq_annotation_assignments_draft_annotator"),
    )

    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False
    )
    annotator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("annotators.id", ondelete="CASCADE"), nullable=False
    )
    batch: Mapped[str] = mapped_column(String(16), nullable=False)
    overlap: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default="false")
    position: Mapped[int] = mapped_column(Integer(), nullable=False)
    served_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Label(UUIDPKMixin, CreatedAtMixin, Base):
    """A rubric label (docs/labelling-rubric.md). `acceptable` is computed by PostgreSQL
    from `label` (A or M), so the binary target can never disagree with the label."""

    __tablename__ = "labels"
    __table_args__ = (
        CheckConstraint("label IN ('A','M','R','W')", name="ck_labels_label"),
        CheckConstraint("(label IS NULL) = (skipped_reason IS NOT NULL)", name="ck_labels_label_or_skip"),
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("annotation_assignments.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    label: Mapped[str | None] = mapped_column(String(1), nullable=True)
    acceptable: Mapped[bool | None] = mapped_column(Boolean(), Computed("label IN ('A','M')", persisted=True))
    reason_codes: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    skipped_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    time_taken_ms: Mapped[int] = mapped_column(Integer(), nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(8), nullable=False)

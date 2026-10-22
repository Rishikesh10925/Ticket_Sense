import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class StudyParticipant(UUIDPKMixin, CreatedAtMixin, Base):
    """A user-study participant (migration 0023). Exports and reports use `code` only."""

    __tablename__ = "study_participants"
    __table_args__ = (
        CheckConstraint("\"order\" IN ('manual_first','workbench_first')", name="ck_study_participants_order"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    order: Mapped[str] = mapped_column(String(16), nullable=False)


class StudyTask(UUIDPKMixin, CreatedAtMixin, Base):
    """One study ticket in one condition. Lane, score and reasons are fixed at creation."""

    __tablename__ = "study_tasks"
    __table_args__ = (
        UniqueConstraint("participant_id", "position", name="uq_study_tasks_participant_position"),
        CheckConstraint("ticket_set IN ('A','B')", name="ck_study_tasks_set"),
        CheckConstraint("condition IN ('manual','workbench')", name="ck_study_tasks_condition"),
        CheckConstraint("lane IN ('fast','assisted','escalate')", name="ck_study_tasks_lane"),
        CheckConstraint("action IS NULL OR action IN ('accept','edit','write','escalate')",
                        name="ck_study_tasks_action"),
    )

    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_participants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drafts.id"), nullable=False)
    benchmark_ticket_id: Mapped[str] = mapped_column(String(16), nullable=False)
    ticket_set: Mapped[str] = mapped_column(String(1), nullable=False)
    condition: Mapped[str] = mapped_column(String(16), nullable=False)
    position: Mapped[int] = mapped_column(Integer(), nullable=False)
    lane: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    reasons: Mapped[list] = mapped_column(JSONB(), nullable=False)
    served_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action: Mapped[str | None] = mapped_column(String(16), nullable=True)
    final_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    time_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)

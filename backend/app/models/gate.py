import uuid

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, String, false
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class GateThresholds(UUIDPKMixin, CreatedAtMixin, Base):
    """A versioned, certified pair of lane thresholds (migration 0021). One is active."""

    __tablename__ = "gate_thresholds"
    __table_args__ = (CheckConstraint("label_source IN ('human','judge')", name="ck_gate_thresholds_label_source"),)

    version: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    label_source: Mapped[str] = mapped_column(String(16), nullable=False)
    alpha_fast: Mapped[float] = mapped_column(Float(), nullable=False)
    alpha_assisted: Mapped[float] = mapped_column(Float(), nullable=False)
    delta: Mapped[float] = mapped_column(Float(), nullable=False)
    fast_threshold: Mapped[float | None] = mapped_column(Float(), nullable=True)
    assisted_threshold: Mapped[float | None] = mapped_column(Float(), nullable=True)
    calibration: Mapped[dict] = mapped_column(JSONB(), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=false())


class GateDecision(UUIDPKMixin, CreatedAtMixin, Base):
    """One gate decision for one draft, with everything needed to explain it later."""

    __tablename__ = "gate_decisions"
    __table_args__ = (CheckConstraint("lane IN ('fast','assisted','escalate')", name="ck_gate_decisions_lane"),)

    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    thresholds_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gate_thresholds.id"), nullable=True
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    lane: Mapped[str] = mapped_column(String(16), nullable=False)
    reasons: Mapped[list] = mapped_column(JSONB(), nullable=False)

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class RetrievalRun(UUIDPKMixin, CreatedAtMixin, Base):
    """One retrieval for one ticket (migration 0013). `ticket_id` is null for offline
    benchmark runs, which are not stored here."""

    __tablename__ = "retrieval_runs"

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text(), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    reranked: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    config_version: Mapped[str] = mapped_column(String(32), nullable=False)
    probe_top1_similarity: Mapped[float | None] = mapped_column(Float(), nullable=True)
    probe_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    latency_ms: Mapped[dict] = mapped_column(JSONB(), nullable=False)


class RetrievalHit(UUIDPKMixin, CreatedAtMixin, Base):
    """One candidate chunk of a run with every score. `final_rank` is 1..k for the
    evidence actually passed on, null for candidates that did not make the cut."""

    __tablename__ = "retrieval_hits"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kb_chunks.id", ondelete="SET NULL"), nullable=True
    )
    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_base.id", ondelete="SET NULL"), nullable=True
    )
    final_rank: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    keyword_rank: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    keyword_score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    dense_rank: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    dense_score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    fused_score: Mapped[float] = mapped_column(Float(), nullable=False)
    rerank_score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    text: Mapped[str] = mapped_column(Text(), nullable=False)

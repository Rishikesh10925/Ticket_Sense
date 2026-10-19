import uuid

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class BenchmarkTicket(CreatedAtMixin, Base):
    """A benchmark ticket loaded into the database for drafting and labelling
    (migration 0014). Type, gold articles and split are never sent to reviewers."""

    __tablename__ = "benchmark_tickets"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    benchmark_version: Mapped[str] = mapped_column(String(16), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(16), nullable=False)
    subject: Mapped[str] = mapped_column(Text(), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    attachment_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    department: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(String(4), nullable=False)
    gold_articles: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False)
    split: Mapped[str] = mapped_column(String(8), nullable=False)


class Draft(UUIDPKMixin, CreatedAtMixin, Base):
    """A structured, cited draft for a live or a benchmark ticket (migration 0014)."""

    __tablename__ = "drafts"
    __table_args__ = (
        CheckConstraint(
            "(ticket_id IS NOT NULL) != (benchmark_ticket_id IS NOT NULL)", name="ck_drafts_exactly_one_ticket"
        ),
        ForeignKeyConstraint(
            ["benchmark_ticket_id", "benchmark_version"],
            ["benchmark_tickets.id", "benchmark_tickets.benchmark_version"],
        ),
    )

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True
    )
    benchmark_ticket_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    benchmark_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    retrieval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="SET NULL"), nullable=True
    )
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_valid: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    can_answer: Mapped[bool | None] = mapped_column(Boolean(), nullable=True)
    steps: Mapped[list] = mapped_column(JSONB(), nullable=False)  # [{"text": str, "citations": [int]}]
    missing_information: Mapped[list] = mapped_column(JSONB(), nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB(), nullable=False)  # [{"n", "article_key", "title", "text"}]
    raw_text: Mapped[str] = mapped_column(Text(), nullable=False)
    groundedness: Mapped[float | None] = mapped_column(Float(), nullable=True)


class DraftClaim(UUIDPKMixin, CreatedAtMixin, Base):
    """One atomic claim of a draft step, with the passages it cites and its entailment
    support score from the NLI checker (Week 5)."""

    __tablename__ = "draft_claims"

    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer(), nullable=False)
    claim_index: Mapped[int] = mapped_column(Integer(), nullable=False)
    text: Mapped[str] = mapped_column(Text(), nullable=False)
    cited: Mapped[list[int]] = mapped_column(ARRAY(Integer()), nullable=False)
    support: Mapped[float | None] = mapped_column(Float(), nullable=True)

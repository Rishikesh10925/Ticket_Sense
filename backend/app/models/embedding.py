import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin

# Matches sentence-transformers/all-MiniLM-L6-v2 (see docs/architecture.md).
EMBEDDING_DIM = 384


class Embedding(UUIDPKMixin, CreatedAtMixin, Base):
    """A retrievable evidence chunk — either a knowledge-base article or a resolved
    ticket (see docs/retrieval.md). Exactly one of knowledge_base_id/ticket_id is set;
    both are nullable rather than using a single polymorphic FK, since pgvector/
    SQLAlchemy don't need anything fancier for two source tables.
    """

    __tablename__ = "embeddings"
    __table_args__ = (
        CheckConstraint(
            "(knowledge_base_id IS NOT NULL) != (ticket_id IS NOT NULL)",
            name="ck_embeddings_exactly_one_source",
        ),
    )

    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=True, index=True
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    chunk_text: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

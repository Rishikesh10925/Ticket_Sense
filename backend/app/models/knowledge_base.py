import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class KnowledgeBase(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "knowledge_base"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # V2 article metadata (migration 0011, docs/kb-article-template.md). article_key is
    # the template id (NET-VPN-001); null for admin-authored articles. Withheld-topic
    # articles are stored with served=False and never retrieved.
    article_key: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    served: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text("true"))
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="1")

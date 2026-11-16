import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, true
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin

# The ticket fields a portal's field_map may refer to (see app/routers/assist.py).
PORTAL_FIELDS = ("subject", "description", "category", "priority", "name", "email", "ticket_ref")


class ComplaintPortal(UUIDPKMixin, CreatedAtMixin, Base):
    """Where the browser extension sends a ticket the knowledge base cannot answer
    (migration 0024). One per department; a portal with no department is the default."""

    __tablename__ = "complaint_portals"

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    # {"subject": "#subject", ...}: ticket field -> CSS selector on the portal's form.
    field_map: Mapped[dict] = mapped_column(JSONB(), nullable=False, server_default="{}")
    # CSS selector of the reference number on the page shown after the user submits.
    reference_selector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=true())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

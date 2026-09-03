from sqlalchemy import CheckConstraint, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin

# Score below which the confidence gate (Week 9) escalates a ticket instead of
# showing its draft to a reviewer. 0.5 is a neutral starting point — a coin flip —
# pending the Week 8 Team Integration review that sets real per-department values;
# see docs/team-integration-week8.md.
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


class Department(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        CheckConstraint(
            "confidence_threshold >= 0 AND confidence_threshold <= 1", name="ck_departments_confidence_threshold"
        ),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(
        Numeric(), nullable=False, server_default=str(DEFAULT_CONFIDENCE_THRESHOLD)
    )

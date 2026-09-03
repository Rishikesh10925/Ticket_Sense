"""ticket escalated status

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-03 07:58:18.211673

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: autogenerate also proposed dropping ix_embeddings_embedding_hnsw here —
    # the same false positive documented in migrations 0005/0006/0007 (raw op.execute
    # index, not visible to SQLAlchemy's metadata). Deliberately not included below.
    #
    # Alembic's autogenerate doesn't reliably diff CheckConstraint bodies (it detected
    # no change here despite ck_tickets_status's allowed values changing in
    # app/models/ticket.py), so this constraint swap is hand-written: drop the old
    # constraint and recreate it with 'escalated' added, for the Week 9 confidence gate
    # (see docs/langgraph-pipeline.md and app/services/ticket_lifecycle.py).
    op.drop_constraint('ck_tickets_status', 'tickets', type_='check')
    op.create_check_constraint(
        'ck_tickets_status',
        'tickets',
        "status IN ('submitted','classified','routed','drafted','reviewed','escalated','closed')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_tickets_status', 'tickets', type_='check')
    op.create_check_constraint(
        'ck_tickets_status',
        'tickets',
        "status IN ('submitted','classified','routed','drafted','reviewed','closed')",
    )

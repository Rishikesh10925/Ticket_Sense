"""ticket lifecycle states

Revises the tickets.status values to the Week 3 lifecycle state machine
(submitted -> classified -> routed -> drafted -> reviewed -> closed), replacing the
placeholder (open/in_review/resolved/escalated/closed) set from the Week 2 schema.
See backend/app/services/ticket_lifecycle.py and docs/ticket-lifecycle.md.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20 14:41:27.723744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Any row not already in a state shared by both sets falls back to 'submitted'
    # rather than being left in a now-invalid state. 'closed' is shared by both sets.
    op.execute(
        "UPDATE tickets SET status = 'submitted' "
        "WHERE status NOT IN ('submitted', 'classified', 'routed', 'drafted', 'reviewed', 'closed')"
    )
    op.drop_constraint("ck_tickets_status", "tickets", type_="check")
    op.create_check_constraint(
        "ck_tickets_status",
        "tickets",
        "status IN ('submitted','classified','routed','drafted','reviewed','closed')",
    )
    op.alter_column("tickets", "status", server_default="submitted")


def downgrade() -> None:
    op.execute(
        "UPDATE tickets SET status = 'open' "
        "WHERE status NOT IN ('open', 'in_review', 'resolved', 'escalated', 'closed')"
    )
    op.drop_constraint("ck_tickets_status", "tickets", type_="check")
    op.create_check_constraint(
        "ck_tickets_status",
        "tickets",
        "status IN ('open','in_review','resolved','escalated','closed')",
    )
    op.alter_column("tickets", "status", server_default="open")

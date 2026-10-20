"""ticket lane and escalation tier

Roadmap Week 9 (Rishikesh): the confidence gate now routes live tickets. Each ticket
records the lane it was assigned (fast, assisted or escalate), and each escalation its
tier: `senior` when the gate withheld the draft, `admin` when an engineer escalated or
doubted after reviewing one (Blueprint V2 §9.1).

Revision ID: 0022
Revises: 0021
Create Date: 2026-12-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0022'
down_revision: Union[str, None] = '0021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('lane', sa.String(16), nullable=True))
    op.create_check_constraint('ck_tickets_lane', 'tickets', "lane IS NULL OR lane IN ('fast','assisted','escalate')")
    op.create_index('ix_tickets_lane', 'tickets', ['lane'])
    op.add_column('escalations', sa.Column('tier', sa.String(16), nullable=False, server_default='admin'))
    op.create_check_constraint('ck_escalations_tier', 'escalations', "tier IN ('senior','admin')")


def downgrade() -> None:
    op.drop_constraint('ck_escalations_tier', 'escalations', type_='check')
    op.drop_column('escalations', 'tier')
    op.drop_index('ix_tickets_lane', table_name='tickets')
    op.drop_constraint('ck_tickets_lane', 'tickets', type_='check')
    op.drop_column('tickets', 'lane')

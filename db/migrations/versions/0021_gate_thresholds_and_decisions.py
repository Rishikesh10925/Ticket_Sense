"""gate: versioned lane thresholds and a log of every gate decision

Blueprint V2 §9 stage 8 and §13.4; Roadmap Week 8 (Rishikesh). Thresholds are rows,
never constants: each set records the model it belongs to, the label source it was
certified on, alpha and delta, and the certified thresholds. Exactly one set is active.
Every decision the gate makes is logged with the score, lane, top reasons and the
threshold set used, so any decision can be explained later even after recalibration.

Revision ID: 0021
Revises: 0020
Create Date: 2026-12-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0021'
down_revision: Union[str, None] = '0020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'gate_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('version', sa.String(32), nullable=False, unique=True),
        sa.Column('model_version', sa.String(64), nullable=False),
        sa.Column('label_source', sa.String(16), nullable=False),
        sa.Column('alpha_fast', sa.Float(), nullable=False),
        sa.Column('alpha_assisted', sa.Float(), nullable=False),
        sa.Column('delta', sa.Float(), nullable=False),
        sa.Column('fast_threshold', sa.Float(), nullable=True),
        sa.Column('assisted_threshold', sa.Float(), nullable=True),
        sa.Column('calibration', postgresql.JSONB(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("label_source IN ('human','judge')", name='ck_gate_thresholds_label_source'),
    )
    # At most one active threshold set.
    op.create_index('uq_gate_thresholds_active', 'gate_thresholds', ['active'], unique=True,
                    postgresql_where=sa.text('active'))
    op.create_table(
        'gate_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drafts.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('thresholds_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('gate_thresholds.id'), nullable=True),
        sa.Column('model_version', sa.String(64), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('lane', sa.String(16), nullable=False),
        sa.Column('reasons', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("lane IN ('fast','assisted','escalate')", name='ck_gate_decisions_lane'),
    )
    op.create_index('ix_gate_decisions_draft_id', 'gate_decisions', ['draft_id'])


def downgrade() -> None:
    op.drop_index('ix_gate_decisions_draft_id', table_name='gate_decisions')
    op.drop_table('gate_decisions')
    op.drop_index('uq_gate_thresholds_active', table_name='gate_thresholds')
    op.drop_table('gate_thresholds')

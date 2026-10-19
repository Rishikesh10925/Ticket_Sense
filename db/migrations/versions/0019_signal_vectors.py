"""signal vectors: the confidence model's inputs for each draft

Blueprint V2 §9 stage 6 and §13.2; Roadmap Week 7. One row per draft and feature
version, written by the live pipeline and by the offline batch, so training and serving
read the same features.

Revision ID: 0019
Revises: 0018
Create Date: 2026-12-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0019'
down_revision: Union[str, None] = '0018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'signal_vectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drafts.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('feature_version', sa.String(32), nullable=False),
        sa.Column('features', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('draft_id', 'feature_version', name='uq_signal_vectors_draft_version'),
    )
    op.create_index('ix_signal_vectors_draft_id', 'signal_vectors', ['draft_id'])


def downgrade() -> None:
    op.drop_index('ix_signal_vectors_draft_id', table_name='signal_vectors')
    op.drop_table('signal_vectors')

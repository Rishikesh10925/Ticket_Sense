"""retrieval_runs and retrieval_hits: every retrieval with every score

Blueprint V2 §10.1 (retrieval_runs, retrieval_hits: per-ticket ranked passages with
keyword, dense, fused and reranker scores) and Roadmap Week 4 ("log every retrieval
run"). The evidence an engineer sees is read back from the run the pipeline logged, so
what is shown is exactly what the draft and the confidence model used.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0013'
down_revision: Union[str, None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'retrieval_runs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ticket_id', sa.UUID(), nullable=True),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(length=16), nullable=False),
        sa.Column('reranked', sa.Boolean(), nullable=False),
        sa.Column('config_version', sa.String(length=32), nullable=False),
        sa.Column('probe_top1_similarity', sa.Float(), nullable=True),
        sa.Column('probe_department_id', sa.UUID(), nullable=True),
        sa.Column('latency_ms', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_retrieval_runs_ticket_id', 'retrieval_runs', ['ticket_id'])
    op.create_table(
        'retrieval_hits',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=True),
        sa.Column('knowledge_base_id', sa.UUID(), nullable=True),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.Column('keyword_rank', sa.Integer(), nullable=True),
        sa.Column('keyword_score', sa.Float(), nullable=True),
        sa.Column('dense_rank', sa.Integer(), nullable=True),
        sa.Column('dense_score', sa.Float(), nullable=True),
        sa.Column('fused_score', sa.Float(), nullable=False),
        sa.Column('rerank_score', sa.Float(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['retrieval_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['kb_chunks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_base.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_retrieval_hits_run_id', 'retrieval_hits', ['run_id'])


def downgrade() -> None:
    op.drop_table('retrieval_hits')
    op.drop_table('retrieval_runs')

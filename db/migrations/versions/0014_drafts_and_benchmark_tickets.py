"""benchmark_tickets, drafts, draft_claims

Blueprint V2 §10.1: drafts (structured draft, citations, can-answer flag) and
draft_claims (atomic claims with per-claim entailment score). A draft belongs either to
a live ticket or to a benchmark ticket (offline runs that feed labelling and evaluation).
`evidence` snapshots the exact passages the model was given, numbered as in the prompt,
so the annotation tool can show reviewers what the model saw.

Brought forward from Week 5 so the Week 4 annotation tool v0 has drafts to serve.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0014'
down_revision: Union[str, None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'benchmark_tickets',
        sa.Column('id', sa.String(length=16), nullable=False),
        sa.Column('benchmark_version', sa.String(length=16), nullable=False),
        sa.Column('group_id', sa.String(length=16), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('attachment_text', sa.Text(), nullable=True),
        sa.Column('department', sa.String(length=32), nullable=False),
        sa.Column('priority', sa.String(length=16), nullable=False),
        sa.Column('type', sa.String(length=4), nullable=False),
        sa.Column('gold_articles', postgresql.ARRAY(sa.String(length=32)), nullable=False),
        sa.Column('split', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', 'benchmark_version'),
    )
    op.create_table(
        'drafts',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ticket_id', sa.UUID(), nullable=True),
        sa.Column('benchmark_ticket_id', sa.String(length=16), nullable=True),
        sa.Column('benchmark_version', sa.String(length=16), nullable=True),
        sa.Column('retrieval_run_id', sa.UUID(), nullable=True),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('prompt_version', sa.String(length=32), nullable=False),
        sa.Column('schema_valid', sa.Boolean(), nullable=False),
        sa.Column('can_answer', sa.Boolean(), nullable=True),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('missing_information', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('groundedness', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            '(ticket_id IS NOT NULL) != (benchmark_ticket_id IS NOT NULL)', name='ck_drafts_exactly_one_ticket'
        ),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['benchmark_ticket_id', 'benchmark_version'],
            ['benchmark_tickets.id', 'benchmark_tickets.benchmark_version'],
        ),
        sa.ForeignKeyConstraint(['retrieval_run_id'], ['retrieval_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_drafts_ticket_id', 'drafts', ['ticket_id'])
    op.create_index('ix_drafts_benchmark_ticket', 'drafts', ['benchmark_ticket_id', 'benchmark_version'])
    op.create_table(
        'draft_claims',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('draft_id', sa.UUID(), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('claim_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('cited', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('support', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_draft_claims_draft_id', 'draft_claims', ['draft_id'])


def downgrade() -> None:
    op.drop_table('draft_claims')
    op.drop_table('drafts')
    op.drop_table('benchmark_tickets')

"""judge verdicts: LLM-judge labels for benchmark drafts

Blueprint V2 §11.6 and Roadmap Weeks 5 and 7. The judge's rubric label for each draft,
kept apart from human `labels` so the two can never be mixed up: judge labels give
training volume, headline numbers use human labels only, and the judge is reported
with its agreement against them.

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0018'
down_revision: Union[str, None] = '0017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'judge_verdicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drafts.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('label', sa.String(1), nullable=False),
        sa.Column('acceptable', sa.Boolean(), sa.Computed("label IN ('A','M')", persisted=True)),
        sa.Column('critical_problem', sa.Boolean(), nullable=False),
        sa.Column('missing_key_facts', postgresql.JSONB(), nullable=False),
        sa.Column('contradicted_key_facts', postgresql.JSONB(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('model', sa.String(64), nullable=False),
        sa.Column('prompt_version', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("label IN ('A','M','R','W')", name='ck_judge_verdicts_label'),
        sa.UniqueConstraint('draft_id', 'model', 'prompt_version', name='uq_judge_verdicts_draft_model_prompt'),
    )
    op.create_index('ix_judge_verdicts_draft_id', 'judge_verdicts', ['draft_id'])


def downgrade() -> None:
    op.drop_index('ix_judge_verdicts_draft_id', table_name='judge_verdicts')
    op.drop_table('judge_verdicts')

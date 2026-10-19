"""annotation tool: annotator role, annotators, assignments, labels

docs/annotation-tool.md (Week 3 design), Blueprint V2 §11.6 and Appendix A. `annotator`
is a restricted account type for outside reviewers, not a product role: it can only use
the /annotate endpoints. Labels are never overwritten; `acceptable` is derived from the
rubric label in the database so it cannot disagree with it.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0015'
down_revision: Union[str, None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_role', 'users', "role IN ('end_user','department_engineer','admin','annotator')"
    )
    op.create_table(
        'annotators',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('pseudonym', sa.String(length=16), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('pseudonym'),
    )
    op.create_table(
        'annotation_assignments',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('draft_id', sa.UUID(), nullable=False),
        sa.Column('annotator_id', sa.UUID(), nullable=False),
        sa.Column('batch', sa.String(length=16), nullable=False),
        sa.Column('overlap', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('served_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['annotator_id'], ['annotators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('draft_id', 'annotator_id', name='uq_assignment_draft_annotator'),
    )
    op.create_index('ix_assignments_annotator_position', 'annotation_assignments', ['annotator_id', 'position'])
    op.create_table(
        'labels',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('label', sa.String(length=1), nullable=True),
        sa.Column(
            'acceptable',
            sa.Boolean(),
            sa.Computed("label IN ('A','M')", persisted=True),
            nullable=True,
        ),
        sa.Column('reason_codes', postgresql.ARRAY(sa.String(length=32)), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('skipped_reason', sa.Text(), nullable=True),
        sa.Column('time_taken_ms', sa.Integer(), nullable=False),
        sa.Column('rubric_version', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("label IN ('A','M','R','W')", name='ck_labels_label'),
        sa.CheckConstraint('(label IS NULL) = (skipped_reason IS NOT NULL)', name='ck_labels_label_or_skip'),
        sa.ForeignKeyConstraint(['assignment_id'], ['annotation_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id'),
    )


def downgrade() -> None:
    op.drop_table('labels')
    op.drop_table('annotation_assignments')
    op.drop_table('annotators')
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint('ck_users_role', 'users', "role IN ('end_user','department_engineer','admin')")

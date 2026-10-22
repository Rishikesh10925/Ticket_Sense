"""user study: participant role, participants and tasks

Roadmap Week 11 (Aashritha: "run the user study with six to eight participants, two
conditions, 20 tickets each"; docs/study/user-study/README.md). `participant` is a
restricted account type like `annotator`: it can only use the /study screen. Each task is
one study ticket in one condition. The lane, score and reasons are fixed when the task is
created, so every participant sees the same stimulus; the server records when a task was
served and submitted, so handling time is not measured in the browser.

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0023'
down_revision: Union[str, None] = '0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_role', 'users', "role IN ('end_user','department_engineer','admin','annotator','participant')"
    )
    op.create_table(
        'study_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        sa.Column('code', sa.String(8), nullable=False, unique=True),
        sa.Column('order', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("\"order\" IN ('manual_first','workbench_first')", name='ck_study_participants_order'),
    )
    op.create_table(
        'study_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('study_participants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drafts.id'), nullable=False),
        sa.Column('benchmark_ticket_id', sa.String(16), nullable=False),
        sa.Column('ticket_set', sa.String(1), nullable=False),
        sa.Column('condition', sa.String(16), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('lane', sa.String(16), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('reasons', postgresql.JSONB(), nullable=False),
        sa.Column('served_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action', sa.String(16), nullable=True),
        sa.Column('final_reply', sa.Text(), nullable=True),
        sa.Column('time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('participant_id', 'position', name='uq_study_tasks_participant_position'),
        sa.CheckConstraint("ticket_set IN ('A','B')", name='ck_study_tasks_set'),
        sa.CheckConstraint("condition IN ('manual','workbench')", name='ck_study_tasks_condition'),
        sa.CheckConstraint("lane IN ('fast','assisted','escalate')", name='ck_study_tasks_lane'),
        sa.CheckConstraint("action IS NULL OR action IN ('accept','edit','write','escalate')",
                           name='ck_study_tasks_action'),
    )
    op.create_index('ix_study_tasks_participant', 'study_tasks', ['participant_id'])


def downgrade() -> None:
    op.drop_index('ix_study_tasks_participant', table_name='study_tasks')
    op.drop_table('study_tasks')
    op.drop_table('study_participants')
    op.drop_constraint('ck_users_role', 'users', type_='check')
    op.create_check_constraint(
        'ck_users_role', 'users', "role IN ('end_user','department_engineer','admin','annotator')"
    )

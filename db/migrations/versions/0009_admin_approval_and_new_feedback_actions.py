"""admin approval fields on escalations, doubt/resolve feedback actions

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('escalations', sa.Column('admin_decision', sa.Text(), nullable=True))
    op.add_column('escalations', sa.Column('admin_note', sa.Text(), nullable=True))
    op.create_check_constraint(
        'ck_escalations_admin_decision',
        'escalations',
        "admin_decision IN ('approved','rejected')",
    )

    # Alembic's autogenerate doesn't reliably diff CheckConstraint bodies (see
    # migration 0008's note), so this is hand-written: 'doubt' (an engineer unsure
    # about a drafted ticket, sends it back to the admin queue) and 'resolve' (an
    # engineer manually closing out an admin-assigned escalation that never had a
    # draft) join the existing accept/edit/reject/escalate set.
    op.drop_constraint('ck_feedback_action', 'feedback', type_='check')
    op.create_check_constraint(
        'ck_feedback_action',
        'feedback',
        "action IN ('accept','edit','reject','escalate','doubt','resolve')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_feedback_action', 'feedback', type_='check')
    op.create_check_constraint(
        'ck_feedback_action',
        'feedback',
        "action IN ('accept','edit','reject','escalate')",
    )

    op.drop_constraint('ck_escalations_admin_decision', 'escalations', type_='check')
    op.drop_column('escalations', 'admin_note')
    op.drop_column('escalations', 'admin_decision')

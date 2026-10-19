"""feedback: reason codes and time taken

Roadmap Week 7, reviewer workbench. Every engineer decision records structured reason
codes (the same list reviewers use in the annotation tool, docs/labelling-rubric.md)
and how long the decision took, measured by the workbench. Handling time is the
outcome of the Week 11 user study (Blueprint V2 RQ4/H4).

Revision ID: 0020
Revises: 0019
Create Date: 2026-12-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0020'
down_revision: Union[str, None] = '0019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('feedback', sa.Column('reason_codes', postgresql.ARRAY(sa.String(32)), nullable=False,
                                        server_default='{}'))
    op.add_column('feedback', sa.Column('time_taken_ms', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('feedback', 'time_taken_ms')
    op.drop_column('feedback', 'reason_codes')

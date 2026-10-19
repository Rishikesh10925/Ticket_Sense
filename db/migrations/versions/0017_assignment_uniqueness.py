"""annotation assignments: one assignment per (draft, annotator)

Roadmap Week 6, annotation tool v1. The planner never gives a reviewer the same draft
twice (double annotation means two *different* reviewers, adjudication a third); the
database now guarantees it too.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = '0017'
down_revision: Union[str, None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_annotation_assignments_draft_annotator', 'annotation_assignments', ['draft_id', 'annotator_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_annotation_assignments_draft_annotator', 'annotation_assignments', type_='unique')

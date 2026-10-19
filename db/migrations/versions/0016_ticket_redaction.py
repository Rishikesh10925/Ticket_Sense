"""ticket redaction: redacted text and redaction map

Blueprint V2 §9 stage 1 and §16. The pipeline redacts PII before any model call or log
(ai/security/pii.py). The redacted text is what models saw; the map (placeholder ->
original) lets an engineer restore values in a reply. Both live on the ticket row,
which already holds the original text.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0016'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('redacted_text', sa.Text(), nullable=True))
    op.add_column('tickets', sa.Column('redaction_map', postgresql.JSONB(), nullable=True))
    op.add_column('tickets', sa.Column('redactor_version', sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'redactor_version')
    op.drop_column('tickets', 'redaction_map')
    op.drop_column('tickets', 'redacted_text')

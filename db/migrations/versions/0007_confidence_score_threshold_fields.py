"""confidence score threshold fields

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-02 22:54:40.565685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: autogenerate also proposed dropping ix_embeddings_embedding_hnsw here —
    # the same false positive documented in migrations 0005/0006 (that index was
    # created via raw op.execute in migration 0004, so SQLAlchemy's metadata doesn't
    # know about it and autogenerate assumes it shouldn't exist). Deliberately not
    # included below.
    op.add_column('departments', sa.Column('confidence_threshold', sa.Numeric(), server_default='0.5', nullable=False))
    op.create_check_constraint('ck_departments_confidence_threshold', 'departments', 'confidence_threshold >= 0 AND confidence_threshold <= 1')
    op.add_column('tickets', sa.Column('confidence_threshold', sa.Numeric(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'confidence_threshold')
    op.drop_constraint('ck_departments_confidence_threshold', 'departments', type_='check')
    op.drop_column('departments', 'confidence_threshold')

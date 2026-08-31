"""ticket attachment text and ocr confidence

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-31 22:24:42.306343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: autogenerate also proposed dropping ix_embeddings_embedding_hnsw here —
    # the same false positive documented in migration 0005 (that index was created via
    # raw op.execute in migration 0004, so SQLAlchemy's metadata doesn't know about it
    # and autogenerate assumes it shouldn't exist). Deliberately not included below.
    op.add_column('tickets', sa.Column('attachment_text', sa.Text(), nullable=True))
    op.add_column('tickets', sa.Column('ocr_confidence', sa.Numeric(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'ocr_confidence')
    op.drop_column('tickets', 'attachment_text')

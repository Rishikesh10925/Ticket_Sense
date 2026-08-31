"""ticket draft citations

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-31 13:57:57.118126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: autogenerate also proposed dropping ix_embeddings_embedding_hnsw here —
    # a false positive, since that index was created via raw op.execute in migration
    # 0004 (pgvector's HNSW index type isn't expressible as a declarative Column
    # index=True), so SQLAlchemy's metadata doesn't know about it and autogenerate
    # assumes it shouldn't exist. Deliberately not included below.
    op.add_column('tickets', sa.Column('ai_draft_citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'ai_draft_citations')

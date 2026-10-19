"""kb_chunks: section-based KB chunks with an embedding and a full-text vector

Blueprint V2 §10.1 (kb_chunks with embeddings and text-search vectors) and §12.1
(chunk by article section, 150 to 300 tokens; keyword search via PostgreSQL full text,
dense search via pgvector). `tsv` is a generated column, so it can never drift from
`text`. Department scoping happens by joining knowledge_base, inside the SQL.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = '0012'
down_revision: Union[str, None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kb_chunks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('knowledge_base_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('sections', sa.String(length=128), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('n_tokens', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column(
            'tsv',
            sa.dialects.postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', text)", persisted=True),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_base.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_base_id', 'chunk_index', name='uq_kb_chunks_article_index'),
    )
    op.create_index('ix_kb_chunks_knowledge_base_id', 'kb_chunks', ['knowledge_base_id'])
    op.create_index('ix_kb_chunks_tsv', 'kb_chunks', ['tsv'], postgresql_using='gin')
    op.execute("CREATE INDEX ix_kb_chunks_embedding_hnsw ON kb_chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.drop_table('kb_chunks')

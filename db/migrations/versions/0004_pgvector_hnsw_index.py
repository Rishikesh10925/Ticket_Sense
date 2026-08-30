"""pgvector hnsw index

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-30 19:16:16.045463

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # HNSW, not ivfflat: docs/architecture.md's "Resolved decisions" already recorded a
    # real correctness bug from the original migration's ivfflat index — with far fewer
    # rows than its 'lists' parameter assumed, ivfflat's default probes=1 searched a
    # near-empty cluster and returned wrong nearest neighbors. ivfflat's lists needs to
    # be tuned to the actual row count and re-tuned as it grows; HNSW's graph structure
    # doesn't have that degenerate small-table failure mode, so it's the safer default
    # at this table's size (~180 rows now, growing weekly) without needing to pick and
    # revisit a lists value. Defaults (m=16, ef_construction=64) are pgvector's own and
    # are fine at this scale.
    op.execute(
        "CREATE INDEX ix_embeddings_embedding_hnsw ON embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embeddings_embedding_hnsw")

"""v2 knowledge-base article metadata: stable article key, topic, served flag, version

Blueprint V2 §10.1 (kb_documents: department, topic, version, last-updated date) and
§11.4 (withheld topics are left out of the served KB). `article_key` is the template's
`id` (e.g. NET-VPN-001); null for articles an admin creates in the UI. Withheld articles
are stored (they give C1 tickets a reference answer) but retrieval only reads served=true.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0011'
down_revision: Union[str, None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_base', sa.Column('article_key', sa.String(length=32), nullable=True))
    op.add_column('knowledge_base', sa.Column('topic', sa.String(length=64), nullable=True))
    op.add_column(
        'knowledge_base', sa.Column('served', sa.Boolean(), server_default=sa.text('true'), nullable=False)
    )
    op.add_column('knowledge_base', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    op.create_index('ix_knowledge_base_article_key', 'knowledge_base', ['article_key'], unique=True)
    op.create_index('ix_knowledge_base_topic', 'knowledge_base', ['topic'])


def downgrade() -> None:
    op.drop_index('ix_knowledge_base_topic', table_name='knowledge_base')
    op.drop_index('ix_knowledge_base_article_key', table_name='knowledge_base')
    op.drop_column('knowledge_base', 'version')
    op.drop_column('knowledge_base', 'served')
    op.drop_column('knowledge_base', 'topic')
    op.drop_column('knowledge_base', 'article_key')

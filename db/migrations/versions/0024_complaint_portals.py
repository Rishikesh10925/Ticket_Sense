"""complaint portals for the browser extension

Future-enhancement work (README "Future enhancements"): when the knowledge base cannot
answer a ticket, the TicketSense browser extension opens the complaint portal registered
for the ticket's department, fills the form from the ticket and leaves Submit to the
user. `complaint_portals` is the admin-managed registry: one portal per department, plus
at most one default portal (department_id NULL) for tickets that were never routed.
`field_map` maps a ticket field (subject, description, ...) to a CSS selector on the
portal's form; `reference_selector` finds the portal's reference number on the page
shown after the user submits. The ticket keeps that reference.

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0024'
down_revision: Union[str, None] = '0023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'complaint_portals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('department_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=True, unique=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('url', sa.String(512), nullable=False),
        sa.Column('field_map', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('reference_selector', sa.String(255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("url ~ '^https?://'", name='ck_complaint_portals_url'),
    )
    # At most one default portal (no department).
    op.create_index('uq_complaint_portals_default', 'complaint_portals', [sa.text('(department_id IS NULL)')],
                    unique=True, postgresql_where=sa.text('department_id IS NULL'))
    op.add_column('tickets', sa.Column('portal_id', postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey('complaint_portals.id', ondelete='SET NULL'), nullable=True))
    op.add_column('tickets', sa.Column('portal_reference', sa.String(64), nullable=True))
    op.add_column('tickets', sa.Column('portal_submitted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'portal_submitted_at')
    op.drop_column('tickets', 'portal_reference')
    op.drop_column('tickets', 'portal_id')
    op.drop_index('uq_complaint_portals_default', table_name='complaint_portals')
    op.drop_table('complaint_portals')

"""add_phase5_rule_versions_audit_scopes_and_scheduler_leases

Revision ID: c1a9328f4bb0
Revises: b978968a8caa
Create Date: 2026-10-25 18:37:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a9328f4bb0'
down_revision: Union[str, Sequence[str], None] = 'b978968a8caa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Phase 5 Rule Studio lifecycle, version history, audit scopes, and scheduler lease."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. rule_definitions extensions
    if 'rule_definitions' in tables:
        cols = [c['name'] for c in inspector.get_columns('rule_definitions')]
        with op.batch_alter_table('rule_definitions', schema=None) as batch_op:
            if 'status' not in cols:
                batch_op.add_column(sa.Column('status', sa.String(length=32), nullable=False, server_default='PUBLISHED'))
            if 'description' not in cols:
                batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
            if 'created_by_id' not in cols:
                batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
            if 'change_reason' not in cols:
                batch_op.add_column(sa.Column('change_reason', sa.Text(), nullable=True))
            if 'effective_from' not in cols:
                batch_op.add_column(sa.Column('effective_from', sa.DateTime(), nullable=False, server_default=sa.func.now()))

    # 2. rule_version_history table
    if 'rule_version_history' not in tables:
        op.create_table(
            'rule_version_history',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('rule_id', sa.Integer(), sa.ForeignKey('rule_definitions.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('rule_code', sa.String(length=64), nullable=False, index=True),
            sa.Column('version', sa.String(length=16), nullable=False),
            sa.Column('category', sa.String(length=64), nullable=False),
            sa.Column('config_json', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='PUBLISHED'),
            sa.Column('change_reason', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True)
        )

    # 3. audit_events extensions (scoping)
    if 'audit_events' in tables:
        audit_cols = [c['name'] for c in inspector.get_columns('audit_events')]
        with op.batch_alter_table('audit_events', schema=None) as batch_op:
            if 'institution_id' not in audit_cols:
                batch_op.add_column(sa.Column('institution_id', sa.Integer(), nullable=True))
            if 'region' not in audit_cols:
                batch_op.add_column(sa.Column('region', sa.String(length=64), nullable=True))

    # 4. scheduler_leases table
    if 'scheduler_leases' not in tables:
        op.create_table(
            'scheduler_leases',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('lease_name', sa.String(length=64), unique=True, index=True, nullable=False),
            sa.Column('holder_id', sa.String(length=128), nullable=False),
            sa.Column('acquired_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('last_heartbeat', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )


def downgrade() -> None:
    """Downgrade Phase 5 schema additions."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'scheduler_leases' in tables:
        op.drop_table('scheduler_leases')

    if 'rule_version_history' in tables:
        op.drop_table('rule_version_history')

    if 'audit_events' in tables:
        with op.batch_alter_table('audit_events', schema=None) as batch_op:
            batch_op.drop_column('region')
            batch_op.drop_column('institution_id')

    if 'rule_definitions' in tables:
        with op.batch_alter_table('rule_definitions', schema=None) as batch_op:
            batch_op.drop_column('effective_from')
            batch_op.drop_column('change_reason')
            batch_op.drop_column('created_by_id')
            batch_op.drop_column('description')
            batch_op.drop_column('status')

"""add_statutory_orders_table

Revision ID: a8b92c41d305
Revises: f7c81d39e201
Create Date: 2026-10-26 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8b92c41d305'
down_revision: Union[str, Sequence[str], None] = 'f7c81d39e201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with statutory_orders table for formal approval/rejection orders."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'statutory_orders' not in tables:
        op.create_table(
            'statutory_orders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('order_number', sa.String(length=128), nullable=False),
            sa.Column('decision', sa.String(length=32), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('order_date', sa.Date(), nullable=False),
            sa.Column('decision_recorded_at', sa.DateTime(), nullable=False),
            sa.Column('issued_by_id', sa.Integer(), nullable=True),
            sa.Column('issued_by_name', sa.String(length=128), nullable=False),
            sa.Column('issued_by_designation', sa.String(length=128), nullable=False, server_default='Member Secretary / Competent Authority, AICTE'),
            sa.Column('decision_remarks', sa.Text(), nullable=False),
            sa.Column('conditions', sa.JSON(), nullable=False),
            sa.Column('reference_identifiers', sa.JSON(), nullable=False),
            sa.Column('pdf_filename', sa.String(length=255), nullable=False),
            sa.Column('pdf_storage_key', sa.String(length=255), nullable=False),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
            sa.Column('verification_token', sa.String(length=64), nullable=False),
            sa.Column('template_version', sa.String(length=32), nullable=False, server_default='1.0.0'),
            sa.Column('signature_status', sa.String(length=64), nullable=False, server_default='UNSIGNED_PROTOTYPE'),
            sa.Column('signing_provider', sa.String(length=64), nullable=False, server_default='NONE_PROTOTYPE_MODE'),
            sa.Column('signing_metadata', sa.JSON(), nullable=False),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('revoked_by_id', sa.Integer(), nullable=True),
            sa.Column('revocation_reason', sa.Text(), nullable=True),
            sa.Column('superseded_by_order_id', sa.Integer(), nullable=True),
            sa.Column('superseded_at', sa.DateTime(), nullable=True),
            sa.Column('superseding_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['issued_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['revoked_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['superseded_by_order_id'], ['statutory_orders.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_statutory_orders_id'), 'statutory_orders', ['id'], unique=False)
        op.create_index(op.f('ix_statutory_orders_application_id'), 'statutory_orders', ['application_id'], unique=False)
        op.create_index(op.f('ix_statutory_orders_institution_id'), 'statutory_orders', ['institution_id'], unique=False)
        op.create_index(op.f('ix_statutory_orders_order_number'), 'statutory_orders', ['order_number'], unique=True)
        op.create_index(op.f('ix_statutory_orders_decision'), 'statutory_orders', ['decision'], unique=False)
        op.create_index(op.f('ix_statutory_orders_status'), 'statutory_orders', ['status'], unique=False)
        op.create_index(op.f('ix_statutory_orders_checksum_sha256'), 'statutory_orders', ['checksum_sha256'], unique=False)
        op.create_index(op.f('ix_statutory_orders_verification_token'), 'statutory_orders', ['verification_token'], unique=True)


def downgrade() -> None:
    """Downgrade schema to remove statutory_orders table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'statutory_orders' in tables:
        op.drop_index(op.f('ix_statutory_orders_verification_token'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_checksum_sha256'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_status'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_decision'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_order_number'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_institution_id'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_application_id'), table_name='statutory_orders')
        op.drop_index(op.f('ix_statutory_orders_id'), table_name='statutory_orders')
        op.drop_table('statutory_orders')

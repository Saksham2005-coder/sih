"""add_notification_outbox_table

Revision ID: b2c3d4e5f601
Revises: a8b92c41d305
Create Date: 2026-10-27 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f601'
down_revision: Union[str, Sequence[str], None] = 'a8b92c41d305'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with notification_outbox table and link notifications.outbox_id."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'notification_outbox' not in tables:
        op.create_table(
            'notification_outbox',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('idempotency_key', sa.String(length=160), nullable=False),
            sa.Column('correlation_id', sa.String(length=64), nullable=False),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('entity_type', sa.String(length=64), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=True),
            sa.Column('region', sa.String(length=64), nullable=True),
            sa.Column('recipient_role', sa.String(length=64), nullable=True),
            sa.Column('recipient_user_id', sa.Integer(), nullable=True),
            sa.Column('recipient_email', sa.String(length=255), nullable=True),
            sa.Column('recipient_phone', sa.String(length=32), nullable=True),
            sa.Column('channel', sa.String(length=32), nullable=False),
            sa.Column('template_code', sa.String(length=64), nullable=False),
            sa.Column('subject', sa.String(length=255), nullable=False),
            sa.Column('body_text', sa.Text(), nullable=False),
            sa.Column('body_html', sa.Text(), nullable=True),
            sa.Column('link_url', sa.String(length=255), nullable=True),
            sa.Column('payload_json', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=32), server_default='QUEUED', nullable=False),
            sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('max_attempts', sa.Integer(), server_default='4', nullable=False),
            sa.Column('next_retry_at', sa.DateTime(), nullable=True),
            sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
            sa.Column('last_error_category', sa.String(length=64), nullable=True),
            sa.Column('last_error_message', sa.Text(), nullable=True),
            sa.Column('provider_message_id', sa.String(length=128), nullable=True),
            sa.Column('provider_response', sa.Text(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notification_outbox_id'), 'notification_outbox', ['id'], unique=False)
        op.create_index(op.f('ix_notification_outbox_idempotency_key'), 'notification_outbox', ['idempotency_key'], unique=True)
        op.create_index(op.f('ix_notification_outbox_correlation_id'), 'notification_outbox', ['correlation_id'], unique=False)
        op.create_index(op.f('ix_notification_outbox_event_type'), 'notification_outbox', ['event_type'], unique=False)
        op.create_index(op.f('ix_notification_outbox_entity_type'), 'notification_outbox', ['entity_type'], unique=False)
        op.create_index(op.f('ix_notification_outbox_entity_id'), 'notification_outbox', ['entity_id'], unique=False)
        op.create_index(op.f('ix_notification_outbox_institution_id'), 'notification_outbox', ['institution_id'], unique=False)
        op.create_index(op.f('ix_notification_outbox_region'), 'notification_outbox', ['region'], unique=False)
        op.create_index(op.f('ix_notification_outbox_recipient_role'), 'notification_outbox', ['recipient_role'], unique=False)
        op.create_index(op.f('ix_notification_outbox_recipient_user_id'), 'notification_outbox', ['recipient_user_id'], unique=False)
        op.create_index(op.f('ix_notification_outbox_channel'), 'notification_outbox', ['channel'], unique=False)
        op.create_index(op.f('ix_notification_outbox_status'), 'notification_outbox', ['status'], unique=False)
        op.create_index(op.f('ix_notification_outbox_next_retry_at'), 'notification_outbox', ['next_retry_at'], unique=False)

    # Check if outbox_id exists on notifications table using batch_alter_table for SQLite compatibility
    if 'notifications' in tables:
        columns = [c['name'] for c in inspector.get_columns('notifications')]
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            if 'outbox_id' not in columns:
                batch_op.add_column(sa.Column('outbox_id', sa.Integer(), nullable=True))
                batch_op.create_index(batch_op.f('ix_notifications_outbox_id'), ['outbox_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'notifications' in tables:
        columns = [c['name'] for c in inspector.get_columns('notifications')]
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            if 'outbox_id' in columns:
                batch_op.drop_index(batch_op.f('ix_notifications_outbox_id'))
                batch_op.drop_column('outbox_id')

    if 'notification_outbox' in tables:
        op.drop_table('notification_outbox')

"""add_phase4_deadline_engine_and_escalation_fields

Revision ID: b978968a8caa
Revises: e5a821bf6290
Create Date: 2026-10-25 16:22:42.018483

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b978968a8caa'
down_revision: Union[str, Sequence[str], None] = 'e5a821bf6290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Phase 4 deadline intelligence, notifications and escalation fields."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. notifications
    if 'notifications' in tables:
        notif_cols = [c['name'] for c in inspector.get_columns('notifications')]
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            if 'recipient_role' not in notif_cols:
                batch_op.add_column(sa.Column('recipient_role', sa.String(length=64), nullable=True))
            if 'entity_type' not in notif_cols:
                batch_op.add_column(sa.Column('entity_type', sa.String(length=64), nullable=True))
            if 'entity_id' not in notif_cols:
                batch_op.add_column(sa.Column('entity_id', sa.Integer(), nullable=True))
            if 'delivery_channel' not in notif_cols:
                batch_op.add_column(sa.Column('delivery_channel', sa.String(length=32), nullable=False, server_default='IN_APP'))
            if 'delivery_status' not in notif_cols:
                batch_op.add_column(sa.Column('delivery_status', sa.String(length=32), nullable=False, server_default='DELIVERED'))
            if 'read_at' not in notif_cols:
                batch_op.add_column(sa.Column('read_at', sa.DateTime(), nullable=True))

    # 2. alert_escalations
    if 'alert_escalations' in tables:
        esc_cols = [c['name'] for c in inspector.get_columns('alert_escalations')]
        with op.batch_alter_table('alert_escalations', schema=None) as batch_op:
            if 'cycle_id' not in esc_cols:
                batch_op.add_column(sa.Column('cycle_id', sa.String(length=64), nullable=True, server_default='1'))
            if 'rule_code' not in esc_cols:
                batch_op.add_column(sa.Column('rule_code', sa.String(length=64), nullable=True))
            if 'rule_version' not in esc_cols:
                batch_op.add_column(sa.Column('rule_version', sa.String(length=16), nullable=True))
            if 'region' not in esc_cols:
                batch_op.add_column(sa.Column('region', sa.String(length=64), nullable=True))
            if 'institution_id' not in esc_cols:
                batch_op.add_column(sa.Column('institution_id', sa.Integer(), nullable=True))
            if 'resolved_at' not in esc_cols:
                batch_op.add_column(sa.Column('resolved_at', sa.DateTime(), nullable=True))
            if 'resolved_reason' not in esc_cols:
                batch_op.add_column(sa.Column('resolved_reason', sa.String(length=255), nullable=True))

    # 3. deadline_engine_runs
    if 'deadline_engine_runs' not in tables:
        op.create_table(
            'deadline_engine_runs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('run_id', sa.String(length=64), nullable=False),
            sa.Column('trigger_mode', sa.String(length=32), nullable=False, server_default='SCHEDULED'),
            sa.Column('scanned_entities', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reminders_created', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('escalations_created', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('duplicates_prevented', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('resolved_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='SUCCESS'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('deadline_engine_runs', schema=None) as batch_op:
            batch_op.create_index('ix_deadline_engine_runs_run_id', ['run_id'], unique=True)
            batch_op.create_index('ix_deadline_engine_runs_id', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'deadline_engine_runs' in tables:
        with op.batch_alter_table('deadline_engine_runs', schema=None) as batch_op:
            batch_op.drop_index('ix_deadline_engine_runs_run_id')
            batch_op.drop_index('ix_deadline_engine_runs_id')
        op.drop_table('deadline_engine_runs')

    if 'alert_escalations' in tables:
        esc_cols = [c['name'] for c in inspector.get_columns('alert_escalations')]
        with op.batch_alter_table('alert_escalations', schema=None) as batch_op:
            for col in ['resolved_reason', 'resolved_at', 'institution_id', 'region', 'rule_version', 'rule_code', 'cycle_id']:
                if col in esc_cols:
                    batch_op.drop_column(col)

    if 'notifications' in tables:
        notif_cols = [c['name'] for c in inspector.get_columns('notifications')]
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            for col in ['read_at', 'delivery_status', 'delivery_channel', 'entity_id', 'entity_type', 'recipient_role']:
                if col in notif_cols:
                    batch_op.drop_column(col)

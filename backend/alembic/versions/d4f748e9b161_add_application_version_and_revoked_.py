"""add_application_version_and_revoked_tokens

Revision ID: d4f748e9b161
Revises: 25e20d1fe338
Create Date: 2026-10-25 13:42:02.900887

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f748e9b161'
down_revision: Union[str, Sequence[str], None] = '25e20d1fe338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with optimistic concurrency version and token revocation table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # Add version column to applications if not already present
    if 'applications' in tables:
        app_cols = [c['name'] for c in inspector.get_columns('applications')]
        if 'version' not in app_cols:
            with op.batch_alter_table('applications', schema=None) as batch_op:
                batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    # Create revoked_tokens table if not exists
    if 'revoked_tokens' not in tables:
        op.create_table(
            'revoked_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('jti', sa.String(length=64), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_revoked_tokens_id'), 'revoked_tokens', ['id'], unique=False)
        op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)
        op.create_index(op.f('ix_revoked_tokens_user_id'), 'revoked_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'revoked_tokens' in tables:
        op.drop_index(op.f('ix_revoked_tokens_user_id'), table_name='revoked_tokens')
        op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
        op.drop_index(op.f('ix_revoked_tokens_id'), table_name='revoked_tokens')
        op.drop_table('revoked_tokens')

    if 'applications' in tables:
        app_cols = [c['name'] for c in inspector.get_columns('applications')]
        if 'version' in app_cols:
            with op.batch_alter_table('applications', schema=None) as batch_op:
                batch_op.drop_column('version')

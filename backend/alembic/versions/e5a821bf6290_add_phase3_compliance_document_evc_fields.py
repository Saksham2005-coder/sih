"""add_phase3_compliance_document_evc_fields

Revision ID: e5a821bf6290
Revises: d4f748e9b161
Create Date: 2026-10-25 15:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a821bf6290'
down_revision: Union[str, Sequence[str], None] = 'd4f748e9b161'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Phase 3 structured fields for compliance, documents, and EVC."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. applications
    if 'applications' in tables:
        app_cols = [c['name'] for c in inspector.get_columns('applications')]
        with op.batch_alter_table('applications', schema=None) as batch_op:
            if 'evc_required' not in app_cols:
                batch_op.add_column(sa.Column('evc_required', sa.Boolean(), nullable=False, server_default='0'))

    # 2. compliance_undertakings
    if 'compliance_undertakings' in tables:
        cu_cols = [c['name'] for c in inspector.get_columns('compliance_undertakings')]
        with op.batch_alter_table('compliance_undertakings', schema=None) as batch_op:
            if 'application_id' not in cu_cols:
                batch_op.add_column(sa.Column('application_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_cu_application_id', 'applications', ['application_id'], ['id'], ondelete='SET NULL')
            if 'rule_code' not in cu_cols:
                batch_op.add_column(sa.Column('rule_code', sa.String(length=64), nullable=True))
            if 'responsible_user_id' not in cu_cols:
                batch_op.add_column(sa.Column('responsible_user_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_cu_responsible_user_id', 'users', ['responsible_user_id'], ['id'], ondelete='SET NULL')
            if 'reviewer_id' not in cu_cols:
                batch_op.add_column(sa.Column('reviewer_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_cu_reviewer_id', 'users', ['reviewer_id'], ['id'], ondelete='SET NULL')
            if 'evidence_type' not in cu_cols:
                batch_op.add_column(sa.Column('evidence_type', sa.String(length=64), nullable=True))
            if 'fulfilled_at' not in cu_cols:
                batch_op.add_column(sa.Column('fulfilled_at', sa.DateTime(), nullable=True))

    # 3. compliance_evidence
    if 'compliance_evidence' in tables:
        ce_cols = [c['name'] for c in inspector.get_columns('compliance_evidence')]
        with op.batch_alter_table('compliance_evidence', schema=None) as batch_op:
            if 'verification_status' not in ce_cols:
                batch_op.add_column(sa.Column('verification_status', sa.String(length=32), nullable=False, server_default='PENDING'))
            if 'verified_by_id' not in ce_cols:
                batch_op.add_column(sa.Column('verified_by_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_ce_verified_by_id', 'users', ['verified_by_id'], ['id'], ondelete='SET NULL')
            if 'verified_at' not in ce_cols:
                batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))
            if 'verification_notes' not in ce_cols:
                batch_op.add_column(sa.Column('verification_notes', sa.Text(), nullable=True))

    # 4. document_records
    if 'document_records' in tables:
        dr_cols = [c['name'] for c in inspector.get_columns('document_records')]
        with op.batch_alter_table('document_records', schema=None) as batch_op:
            if 'application_id' not in dr_cols:
                batch_op.add_column(sa.Column('application_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_dr_application_id', 'applications', ['application_id'], ['id'], ondelete='SET NULL')
            if 'issuing_authority' not in dr_cols:
                batch_op.add_column(sa.Column('issuing_authority', sa.String(length=128), nullable=True))
            if 'valid_from' not in dr_cols:
                batch_op.add_column(sa.Column('valid_from', sa.Date(), nullable=True))
            if 'renewal_required' not in dr_cols:
                batch_op.add_column(sa.Column('renewal_required', sa.Boolean(), nullable=False, server_default='1'))

    # 5. document_versions
    if 'document_versions' in tables:
        dv_cols = [c['name'] for c in inspector.get_columns('document_versions')]
        with op.batch_alter_table('document_versions', schema=None) as batch_op:
            if 'storage_key' not in dv_cols:
                batch_op.add_column(sa.Column('storage_key', sa.String(length=255), nullable=True))
            if 'file_size' not in dv_cols:
                batch_op.add_column(sa.Column('file_size', sa.Integer(), nullable=True))
            if 'mime_type' not in dv_cols:
                batch_op.add_column(sa.Column('mime_type', sa.String(length=64), nullable=True))
            if 'renewal_reason' not in dv_cols:
                batch_op.add_column(sa.Column('renewal_reason', sa.Text(), nullable=True))

    # 6. evc_inspections
    if 'evc_inspections' in tables:
        evc_cols = [c['name'] for c in inspector.get_columns('evc_inspections')]
        with op.batch_alter_table('evc_inspections', schema=None) as batch_op:
            if 'convener_user_id' not in evc_cols:
                batch_op.add_column(sa.Column('convener_user_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_evc_convener_user_id', 'users', ['convener_user_id'], ['id'], ondelete='SET NULL')
            if 'expert_user_id' not in evc_cols:
                batch_op.add_column(sa.Column('expert_user_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_evc_expert_user_id', 'users', ['expert_user_id'], ['id'], ondelete='SET NULL')
            if 'coordinator_id' not in evc_cols:
                batch_op.add_column(sa.Column('coordinator_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_evc_coordinator_id', 'users', ['coordinator_id'], ['id'], ondelete='SET NULL')
            if 'completed_at' not in evc_cols:
                batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))
            if 'completed_by_id' not in evc_cols:
                batch_op.add_column(sa.Column('completed_by_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_evc_completed_by_id', 'users', ['completed_by_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'evc_inspections' in tables:
        with op.batch_alter_table('evc_inspections', schema=None) as batch_op:
            batch_op.drop_column('completed_by_id')
            batch_op.drop_column('completed_at')
            batch_op.drop_column('coordinator_id')
            batch_op.drop_column('expert_user_id')
            batch_op.drop_column('convener_user_id')

    if 'document_versions' in tables:
        with op.batch_alter_table('document_versions', schema=None) as batch_op:
            batch_op.drop_column('renewal_reason')
            batch_op.drop_column('mime_type')
            batch_op.drop_column('file_size')
            batch_op.drop_column('storage_key')

    if 'document_records' in tables:
        with op.batch_alter_table('document_records', schema=None) as batch_op:
            batch_op.drop_column('renewal_required')
            batch_op.drop_column('valid_from')
            batch_op.drop_column('issuing_authority')
            batch_op.drop_column('application_id')

    if 'compliance_evidence' in tables:
        with op.batch_alter_table('compliance_evidence', schema=None) as batch_op:
            batch_op.drop_column('verification_notes')
            batch_op.drop_column('verified_at')
            batch_op.drop_column('verified_by_id')
            batch_op.drop_column('verification_status')

    if 'compliance_undertakings' in tables:
        with op.batch_alter_table('compliance_undertakings', schema=None) as batch_op:
            batch_op.drop_column('fulfilled_at')
            batch_op.drop_column('evidence_type')
            batch_op.drop_column('reviewer_id')
            batch_op.drop_column('responsible_user_id')
            batch_op.drop_column('rule_code')
            batch_op.drop_column('application_id')

    if 'applications' in tables:
        with op.batch_alter_table('applications', schema=None) as batch_op:
            batch_op.drop_column('evc_required')

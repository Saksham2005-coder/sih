"""add_document_intelligence_analyses

Revision ID: f7c81d39e201
Revises: c1a9328f4bb0
Create Date: 2026-10-26 22:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7c81d39e201'
down_revision: Union[str, Sequence[str], None] = 'c1a9328f4bb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Document Intelligence & Evidence Extraction table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'document_analyses' not in tables:
        op.create_table(
            'document_analyses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('document_record_id', sa.Integer(), nullable=True),
            sa.Column('document_version_id', sa.Integer(), nullable=True),
            sa.Column('compliance_evidence_id', sa.Integer(), nullable=True),
            sa.Column('institution_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('idempotency_key', sa.String(length=128), nullable=False),
            sa.Column('extraction_engine', sa.String(length=64), nullable=False),
            sa.Column('engine_version', sa.String(length=32), nullable=False),
            sa.Column('ocr_applied', sa.Boolean(), nullable=False),
            sa.Column('ocr_provider', sa.String(length=64), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=True),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
            sa.Column('page_count', sa.Integer(), nullable=False),
            sa.Column('has_text_layer', sa.Boolean(), nullable=False),
            sa.Column('is_scanned', sa.Boolean(), nullable=False),
            sa.Column('extracted_fields', sa.JSON(), nullable=False),
            sa.Column('cross_check_findings', sa.JSON(), nullable=False),
            sa.Column('overall_confidence', sa.Float(), nullable=False),
            sa.Column('summary_findings', sa.Text(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('reviewer_decision', sa.String(length=32), nullable=True),
            sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('reviewer_remarks', sa.Text(), nullable=True),
            sa.Column('corrected_fields', sa.JSON(), nullable=True),
            sa.Column('processing_started_at', sa.DateTime(), nullable=True),
            sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['compliance_evidence_id'], ['compliance_evidence.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_record_id'], ['document_records.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_analyses_id'), 'document_analyses', ['id'], unique=False)
        op.create_index(op.f('ix_document_analyses_idempotency_key'), 'document_analyses', ['idempotency_key'], unique=True)
        op.create_index(op.f('ix_document_analyses_institution_id'), 'document_analyses', ['institution_id'], unique=False)
        op.create_index(op.f('ix_document_analyses_status'), 'document_analyses', ['status'], unique=False)
        op.create_index(op.f('ix_document_analyses_document_record_id'), 'document_analyses', ['document_record_id'], unique=False)
        op.create_index(op.f('ix_document_analyses_document_version_id'), 'document_analyses', ['document_version_id'], unique=False)
        op.create_index(op.f('ix_document_analyses_compliance_evidence_id'), 'document_analyses', ['compliance_evidence_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove document_analyses table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'document_analyses' in tables:
        op.drop_index(op.f('ix_document_analyses_compliance_evidence_id'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_document_version_id'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_document_record_id'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_status'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_institution_id'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_idempotency_key'), table_name='document_analyses')
        op.drop_index(op.f('ix_document_analyses_id'), table_name='document_analyses')
        op.drop_table('document_analyses')

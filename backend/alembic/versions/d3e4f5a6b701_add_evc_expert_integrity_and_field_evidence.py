"""add_evc_expert_integrity_and_field_evidence

Revision ID: d3e4f5a6b701
Revises: b2c3d4e5f601
Create Date: 2026-10-27 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b701'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f601'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with evc_experts, evc_panel_assignments, evc_field_evidence tables and inspection extensions."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. evc_experts table
    if 'evc_experts' not in tables:
        op.create_table(
            'evc_experts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=32), nullable=True),
            sa.Column('designation', sa.String(length=128), server_default='Professor', nullable=False),
            sa.Column('expertise_categories', sa.JSON(), nullable=False),
            sa.Column('specializations', sa.JSON(), nullable=False),
            sa.Column('current_institution', sa.String(length=255), nullable=False),
            sa.Column('institution_id', sa.Integer(), nullable=True),
            sa.Column('parent_organization', sa.String(length=255), nullable=True),
            sa.Column('district', sa.String(length=64), nullable=True),
            sa.Column('region', sa.String(length=64), server_default='Western', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('availability_status', sa.String(length=32), server_default='AVAILABLE', nullable=False),
            sa.Column('declared_conflicts', sa.JSON(), nullable=False),
            sa.Column('prior_inspections', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evc_experts_email'), 'evc_experts', ['email'], unique=True)
        op.create_index(op.f('ix_evc_experts_id'), 'evc_experts', ['id'], unique=False)
        op.create_index(op.f('ix_evc_experts_region'), 'evc_experts', ['region'], unique=False)

    # 2. Add supplementary columns to evc_inspections
    if 'evc_inspections' in tables:
        evc_cols = [c['name'] for c in inspector.get_columns('evc_inspections')]
        if 'panel_status' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('panel_status', sa.String(length=32), server_default='PENDING_PANEL', nullable=False))
        if 'check_in_at' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('check_in_at', sa.DateTime(), nullable=True))
        if 'check_in_lat' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('check_in_lat', sa.Float(), nullable=True))
        if 'check_in_lon' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('check_in_lon', sa.Float(), nullable=True))
        if 'check_in_accuracy' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('check_in_accuracy', sa.Float(), nullable=True))
        if 'check_in_source' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('check_in_source', sa.String(length=64), nullable=True))
        if 'virtual_meeting_url' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('virtual_meeting_url', sa.String(length=512), nullable=True))
        if 'virtual_recording_url' not in evc_cols:
            op.add_column('evc_inspections', sa.Column('virtual_recording_url', sa.String(length=512), nullable=True))

    # 3. evc_panel_assignments table
    if 'evc_panel_assignments' not in tables:
        op.create_table(
            'evc_panel_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('inspection_id', sa.Integer(), nullable=False),
            sa.Column('expert_id', sa.Integer(), nullable=False),
            sa.Column('panel_role', sa.String(length=32), server_default='EXPERT_MEMBER', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='PROPOSED', nullable=False),
            sa.Column('invited_at', sa.DateTime(), nullable=True),
            sa.Column('responded_at', sa.DateTime(), nullable=True),
            sa.Column('decline_reason', sa.Text(), nullable=True),
            sa.Column('coi_check_result', sa.JSON(), nullable=True),
            sa.Column('override_applied', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('override_reason', sa.Text(), nullable=True),
            sa.Column('override_by_id', sa.Integer(), nullable=True),
            sa.Column('override_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['inspection_id'], ['evc_inspections.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['expert_id'], ['evc_experts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['override_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evc_panel_assignments_id'), 'evc_panel_assignments', ['id'], unique=False)
        op.create_index(op.f('ix_evc_panel_assignments_inspection_id'), 'evc_panel_assignments', ['inspection_id'], unique=False)
        op.create_index(op.f('ix_evc_panel_assignments_expert_id'), 'evc_panel_assignments', ['expert_id'], unique=False)

    # 4. evc_field_evidence table
    if 'evc_field_evidence' not in tables:
        op.create_table(
            'evc_field_evidence',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('inspection_id', sa.Integer(), nullable=False),
            sa.Column('checklist_item_code', sa.String(length=64), nullable=False),
            sa.Column('requirement_title', sa.String(length=255), nullable=False),
            sa.Column('observation_notes', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=32), server_default='COMPLIANT', nullable=False),
            sa.Column('file_url', sa.String(length=512), nullable=True),
            sa.Column('file_hash', sa.String(length=64), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=True),
            sa.Column('file_size_bytes', sa.Integer(), nullable=True),
            sa.Column('evidence_type', sa.String(length=32), server_default='PHOTO', nullable=False),
            sa.Column('captured_by_id', sa.Integer(), nullable=True),
            sa.Column('captured_at', sa.DateTime(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('location_accuracy_meters', sa.Float(), nullable=True),
            sa.Column('location_capture_source', sa.String(length=64), server_default='MANUAL_OFFICER_OVERRIDE', nullable=True),
            sa.Column('location_permission_granted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['inspection_id'], ['evc_inspections.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['captured_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evc_field_evidence_id'), 'evc_field_evidence', ['id'], unique=False)
        op.create_index(op.f('ix_evc_field_evidence_inspection_id'), 'evc_field_evidence', ['inspection_id'], unique=False)


def downgrade() -> None:
    op.drop_table('evc_field_evidence')
    op.drop_table('evc_panel_assignments')
    op.drop_table('evc_experts')

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class EVCExpert(Base):
    """
    Structured registry of authorized EVC Subject Experts and Panel Conveners.
    Stores explicit, auditable provenance data (affiliations, parent trusts, declared conflicts,
    prior inspections) to enforce deterministic, explainable Conflict-of-Interest (COI) policies.
    """
    __tablename__ = "evc_experts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(32), nullable=True)

    # Academic & Domain Credentials
    designation = Column(String(128), default="Professor", nullable=False)
    expertise_categories = Column(JSON, default=list, nullable=False)  # e.g. ["Computer Science", "Artificial Intelligence"]
    specializations = Column(JSON, default=list, nullable=False)       # e.g. ["Cadre Ratio", "Compute Clusters", "Research Labs"]

    # Affiliations & Provenance (Never inferred from name)
    current_institution = Column(String(255), nullable=False)        # E.g. "Indian Institute of Technology Bombay"
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_organization = Column(String(255), nullable=True)         # E.g. "IIT Council" or "Apex Education Society"
    district = Column(String(64), nullable=True)
    region = Column(String(64), default="Western", nullable=False, index=True)

    # Operational Availability
    is_active = Column(Boolean, default=True, nullable=False)
    availability_status = Column(String(32), default="AVAILABLE", nullable=False)  # AVAILABLE, BUSY, ON_LEAVE

    # Explicit Conflict Declarations & Prior Inspection Audit Trail
    # e.g. [{"institution_id": 1, "institution_name": "Apex...", "reason": "Family member employed"}]
    declared_conflicts = Column(JSON, default=list, nullable=False)
    # e.g. [{"institution_id": 1, "institution_name": "Apex...", "inspection_date": "2024-03-15", "role": "EXPERT_MEMBER"}]
    prior_inspections = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    assignments = relationship("EVCPanelAssignment", back_populates="expert")


class EVCInspection(Base):
    __tablename__ = "evc_inspections"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_type = Column(String(32), default="PHYSICAL_ONSITE", nullable=False)  # PHYSICAL_ONSITE, VIRTUAL_REMOTE
    scheduled_date = Column(DateTime, nullable=True, index=True)
    convener_name = Column(String(128), nullable=True)
    expert_member_name = Column(String(128), nullable=True)
    convener_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expert_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    coordinator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(32), default="PENDING_ASSIGNMENT", nullable=False)
    report_url = Column(String(512), nullable=True)
    report_notes = Column(Text, nullable=True)
    recommendation = Column(String(64), nullable=True)  # RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION, DEFICIENCY_NOTED

    # Panel Formation Lifecycle State
    # PENDING_PANEL, INVITATIONS_DISPATCHED, PANEL_CONFIRMED, REASSIGNMENT_REQUIRED
    panel_status = Column(String(32), default="PENDING_PANEL", nullable=False)

    # Inspector Field Check-in & Geolocation Provenance
    check_in_at = Column(DateTime, nullable=True)
    check_in_lat = Column(Float, nullable=True)
    check_in_lon = Column(Float, nullable=True)
    check_in_accuracy = Column(Float, nullable=True)
    check_in_source = Column(String(64), nullable=True)  # BROWSER_GEOLOCATION, MANUAL_OFFICER_OVERRIDE, VIRTUAL_REMOTE

    # Virtual Inspection Integration Boundary
    virtual_meeting_url = Column(String(512), nullable=True)
    virtual_recording_url = Column(String(512), nullable=True)

    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", back_populates="evc_inspections")
    panel_assignments = relationship("EVCPanelAssignment", back_populates="inspection", cascade="all, delete-orphan")
    field_evidence = relationship("EVCFieldEvidence", back_populates="inspection", cascade="all, delete-orphan")


class EVCPanelAssignment(Base):
    """
    Panel member assignment with formal invitation lifecycle:
    PROPOSED -> INVITED -> ACCEPTED | DECLINED | CONFLICTED | REASSIGNED | CANCELLED
    Stores explainable COI audit assessment and authorized administrative overrides.
    """
    __tablename__ = "evc_panel_assignments"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("evc_inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    expert_id = Column(Integer, ForeignKey("evc_experts.id", ondelete="CASCADE"), nullable=False, index=True)

    panel_role = Column(String(32), default="EXPERT_MEMBER", nullable=False)  # CONVENER, EXPERT_MEMBER
    status = Column(String(32), default="PROPOSED", nullable=False)           # PROPOSED, INVITED, ACCEPTED, DECLINED, CONFLICTED, REASSIGNED, CANCELLED

    invited_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    decline_reason = Column(Text, nullable=True)

    # Explainable COI Assessment Breakdown
    coi_check_result = Column(JSON, nullable=True)

    # Operational Override Audit Trail
    override_applied = Column(Boolean, default=False, nullable=False)
    override_reason = Column(Text, nullable=True)
    override_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    override_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("EVCInspection", back_populates="panel_assignments")
    expert = relationship("EVCExpert", back_populates="assignments")


class EVCFieldEvidence(Base):
    """
    Mobile field inspection evidence item.
    Supports checklist linkage, observations, photo/file uploads, SHA-256 tamper-evident hashing,
    and opt-in browser geolocation capture with explicit accuracy metadata.
    """
    __tablename__ = "evc_field_evidence"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("evc_inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    checklist_item_code = Column(String(64), nullable=False)  # E.g. LAND_CAMPUS_AREA, LAB_EQUIPMENT, FIRE_NOC
    requirement_title = Column(String(255), nullable=False)
    observation_notes = Column(Text, nullable=False)
    status = Column(String(32), default="COMPLIANT", nullable=False)  # COMPLIANT, DEFICIENT, NOT_APPLICABLE, PENDING_REVIEW

    # Evidence File & Tamper-Evident Hashing
    file_url = Column(String(512), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256
    file_name = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    evidence_type = Column(String(32), default="PHOTO", nullable=False)  # PHOTO, DOCUMENT, VIRTUAL_RECORDING, CHECKLIST_NOTE

    # Inspector & Geolocation Provenance (Opt-in browser permission)
    captured_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_accuracy_meters = Column(Float, nullable=True)
    location_capture_source = Column(String(64), default="MANUAL_OFFICER_OVERRIDE", nullable=True)  # BROWSER_GEOLOCATION, MANUAL_OFFICER_OVERRIDE, VIRTUAL_REMOTE
    location_permission_granted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    inspection = relationship("EVCInspection", back_populates="field_evidence")

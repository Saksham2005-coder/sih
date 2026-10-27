from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_regional_access
from app.models.user import User
from app.models.evc import EVCInspection, EVCExpert, EVCPanelAssignment, EVCFieldEvidence
from app.models.application import Application
from app.models.institution import Institution
from app.schemas.evc import (
    EVCScheduleRequest,
    EVCReportSubmitRequest,
    EVCInspectionResponse,
    EVCExpertResponse,
    COICheckRequest,
    COICheckResponse,
    COIRuleResult,
    EVCPanelProposeRequest,
    EVCPanelAssignmentResponse,
    EVCInvitationDeclineRequest,
    EVCReassignRequest,
    EVCCheckInRequest,
    EVCFieldEvidenceCreateRequest,
    EVCFieldEvidenceResponse,
)
from app.services.evc_service import EVCService
from app.services.evc_coi_service import EVCConflictService, EVCWorkflowService
from app.core.rbac import check_regional_scope, has_permission, Permission

router = APIRouter(prefix="/evc", tags=["EVC Management"])


def _serialize_panel_assignment(a: EVCPanelAssignment) -> EVCPanelAssignmentResponse:
    expert = a.expert
    return EVCPanelAssignmentResponse(
        id=a.id,
        inspection_id=a.inspection_id,
        expert_id=a.expert_id,
        expert_name=expert.name if expert else None,
        expert_email=expert.email if expert else None,
        expert_institution=expert.current_institution if expert else None,
        panel_role=a.panel_role,
        status=a.status,
        invited_at=a.invited_at,
        responded_at=a.responded_at,
        decline_reason=a.decline_reason,
        coi_check_result=a.coi_check_result,
        override_applied=a.override_applied,
        override_reason=a.override_reason,
        created_at=a.created_at,
        updated_at=a.updated_at
    )


def _serialize_evidence(e: EVCFieldEvidence) -> EVCFieldEvidenceResponse:
    return EVCFieldEvidenceResponse(
        id=e.id,
        inspection_id=e.inspection_id,
        checklist_item_code=e.checklist_item_code,
        requirement_title=e.requirement_title,
        observation_notes=e.observation_notes,
        status=e.status,
        file_url=e.file_url,
        file_hash=e.file_hash,
        file_name=e.file_name,
        file_size_bytes=e.file_size_bytes,
        evidence_type=e.evidence_type,
        captured_by_id=e.captured_by_id,
        captured_at=e.captured_at,
        latitude=e.latitude,
        longitude=e.longitude,
        location_accuracy_meters=e.location_accuracy_meters,
        location_capture_source=e.location_capture_source,
        location_permission_granted=e.location_permission_granted,
        created_at=e.created_at,
        updated_at=e.updated_at
    )


def _serialize_inspection(insp: EVCInspection) -> EVCInspectionResponse:
    app = insp.application
    inst = app.institution if app else None
    return EVCInspectionResponse(
        id=insp.id,
        application_id=insp.application_id,
        application_number=app.application_number if app else None,
        institution_id=app.institution_id if app else None,
        institution_name=inst.name if inst else None,
        region=inst.region if inst else None,
        inspection_type=insp.inspection_type,
        scheduled_date=insp.scheduled_date,
        convener_name=insp.convener_name,
        expert_member_name=insp.expert_member_name,
        coordinator_id=insp.coordinator_id,
        status=insp.status,
        panel_status=insp.panel_status or "PENDING_PANEL",
        check_in_at=insp.check_in_at,
        check_in_lat=insp.check_in_lat,
        check_in_lon=insp.check_in_lon,
        check_in_accuracy=insp.check_in_accuracy,
        check_in_source=insp.check_in_source,
        virtual_meeting_url=insp.virtual_meeting_url,
        virtual_recording_url=insp.virtual_recording_url,
        report_url=insp.report_url,
        report_notes=insp.report_notes,
        recommendation=insp.recommendation,
        completed_at=insp.completed_at,
        completed_by_id=insp.completed_by_id,
        created_at=insp.created_at,
        updated_at=insp.updated_at,
        panel_assignments=[_serialize_panel_assignment(a) for a in (insp.panel_assignments or [])],
        field_evidence=[_serialize_evidence(e) for e in (insp.field_evidence or [])]
    )


def _verify_inspection_access(inspection: EVCInspection, current_user: User):
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)
    app = inspection.application
    if not is_officer:
        if not current_user.institution_id or not app or app.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Unauthorized: Access denied to inspection outside institution")
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if app and app.institution and app.institution.region != current_user.region:
            raise HTTPException(status_code=403, detail=f"Unauthorized: Access denied to region '{app.institution.region}'")


# ==========================================
# QUEUE & SCHEDULE (BACKWARD COMPATIBLE)
# ==========================================

@router.get("/queue", response_model=List[EVCInspectionResponse])
def get_evc_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EVCInspection).join(
        Application, EVCInspection.application_id == Application.id
    ).join(
        Institution, Application.institution_id == Institution.id
    )

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(Institution.region == current_user.region)

    inspections = query.order_by(EVCInspection.scheduled_date.asc().nullslast()).all()
    return [_serialize_inspection(insp) for insp in inspections]


@router.post("/schedule", response_model=EVCInspectionResponse)
@router.post("/inspections", response_model=EVCInspectionResponse)
def schedule_evc_inspection(
    request: EVCScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = EVCService.schedule_inspection(
        db=db,
        application_id=request.application_id,
        inspection_type=request.inspection_type,
        scheduled_date=request.scheduled_date,
        convener_name=request.convener_name,
        expert_member_name=request.expert_member_name,
        actor=current_user
    )
    return _serialize_inspection(inspection)


@router.post("/{id}/submit-report", response_model=EVCInspectionResponse)
@router.post("/inspections/{id}/report", response_model=EVCInspectionResponse)
def submit_evc_report(
    id: int,
    request: EVCReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = EVCService.submit_report(
        db=db,
        inspection_id=id,
        report_url=request.report_url,
        report_notes=request.report_notes,
        recommendation=request.recommendation,
        actor=current_user
    )
    if request.virtual_meeting_url:
        inspection.virtual_meeting_url = request.virtual_meeting_url
    if request.virtual_recording_url:
        inspection.virtual_recording_url = request.virtual_recording_url
        db.commit()
        db.refresh(inspection)

    return _serialize_inspection(inspection)


# ==========================================
# EXPERT REGISTRY & COI ENGINE
# ==========================================

@router.get("/experts", response_model=List[EVCExpertResponse])
def get_evc_experts(
    region: Optional[str] = Query(None),
    availability_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns AICTE EVC expert registry with qualifications, specializations, and conflict history.
    Restricted to authorized officers.
    """
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)
    if not is_officer:
        raise HTTPException(status_code=403, detail="Unauthorized: Expert registry view restricted to officers")

    query = db.query(EVCExpert)

    # Scoping: Regional officer sees experts relevant to their region by default or all if unconstrained
    if region:
        query = query.filter(EVCExpert.region == region)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(or_(EVCExpert.region == current_user.region, EVCExpert.region == "ALL_INDIA"))

    if availability_status:
        query = query.filter(EVCExpert.availability_status == availability_status)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                EVCExpert.name.ilike(s),
                EVCExpert.current_institution.ilike(s),
                EVCExpert.designation.ilike(s)
            )
        )

    experts = query.order_by(EVCExpert.name.asc()).all()
    return experts


@router.get("/experts/{id}", response_model=EVCExpertResponse)
def get_evc_expert_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expert = db.query(EVCExpert).filter(EVCExpert.id == id).first()
    if not expert:
        raise HTTPException(status_code=404, detail="Expert profile not found")
    return expert


@router.post("/coi-check", response_model=COICheckResponse)
def check_conflict_of_interest(
    request: COICheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes explainable conflict-of-interest check against the specified institution application.
    Returns clear rule-by-rule statuses without committing assignments.
    """
    expert = db.query(EVCExpert).filter(EVCExpert.id == request.expert_id).first()
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert #{request.expert_id} not found")

    application = db.query(Application).filter(Application.id == request.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application #{request.application_id} not found")

    assessment = EVCConflictService.evaluate_coi(
        expert=expert,
        application=application,
        cooling_off_years=request.cooling_off_years or 3
    )
    return assessment


# ==========================================
# STRUCTURED ASSIGNMENT LIFECYCLE
# ==========================================

@router.post("/assignments/propose", response_model=EVCPanelAssignmentResponse)
def propose_panel_assignment(
    request: EVCPanelProposeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Proposes an expert for an inspection panel. Automatically runs COI engine.
    If prohibited, requires authorized override with mandatory audit reason.
    """
    assignment = EVCWorkflowService.propose_panel_assignment(
        db=db,
        inspection_id=request.inspection_id,
        expert_id=request.expert_id,
        panel_role=request.panel_role,
        actor=current_user,
        override_reason=request.override_reason
    )
    return _serialize_panel_assignment(assignment)


@router.post("/assignments/{id}/invite", response_model=EVCPanelAssignmentResponse)
def invite_panel_expert(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dispatches formal invitation notice to proposed expert via notification outbox.
    """
    assignment = EVCWorkflowService.invite_expert(
        db=db,
        assignment_id=id,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment)


@router.post("/assignments/{id}/accept", response_model=EVCPanelAssignmentResponse)
def accept_panel_invitation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks invitation ACCEPTED. When both Convener and Expert Member accept, transitions inspection to SCHEDULED.
    """
    assignment = EVCWorkflowService.accept_invitation(
        db=db,
        assignment_id=id,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment)


@router.post("/assignments/{id}/decline", response_model=EVCPanelAssignmentResponse)
def decline_panel_invitation(
    id: int,
    request: EVCInvitationDeclineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Declines invitation with reason. Transitions inspection to REASSIGNMENT_REQUIRED.
    """
    assignment = EVCWorkflowService.decline_invitation(
        db=db,
        assignment_id=id,
        reason=request.reason,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment)


@router.post("/assignments/{id}/reassign", response_model=EVCPanelAssignmentResponse)
def reassign_panel_expert(
    id: int,
    request: EVCReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reassigns a declined or conflicted member to a replacement expert.
    """
    new_assignment = EVCWorkflowService.reassign_panel_member(
        db=db,
        old_assignment_id=id,
        new_expert_id=request.new_expert_id,
        actor=current_user,
        override_reason=request.override_reason
    )
    return _serialize_panel_assignment(new_assignment)


# ==========================================
# MOBILE FIELD INSPECTION & EVIDENCE CAPTURE
# ==========================================

@router.post("/inspections/{id}/check-in", response_model=EVCInspectionResponse)
def check_in_inspection(
    id: int,
    request: EVCCheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Records inspector field check-in with transparent location accuracy provenance.
    Coordinates are recorded without falsely claiming spoof-proof certainty.
    """
    inspection = EVCWorkflowService.check_in_inspection(
        db=db,
        inspection_id=id,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy,
        source=request.source,
        actor=current_user
    )
    return _serialize_inspection(inspection)


@router.post("/inspections/{id}/evidence", response_model=EVCFieldEvidenceResponse)
def record_field_evidence(
    id: int,
    request: EVCFieldEvidenceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Records checklist item observation notes and attaches file evidence with SHA-256 integrity hash.
    Transparently notes location accuracy and permission granted status.
    """
    evidence = EVCWorkflowService.record_field_evidence(
        db=db,
        inspection_id=id,
        checklist_item_code=request.checklist_item_code,
        requirement_title=request.requirement_title,
        observation_notes=request.observation_notes,
        status=request.status,
        file_url=request.file_url,
        file_content=None,
        file_name=request.file_name,
        evidence_type=request.evidence_type,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy,
        source=request.source,
        permission_granted=request.permission_granted,
        actor=current_user
    )
    return _serialize_evidence(evidence)


@router.get("/inspections/{id}/evidence", response_model=List[EVCFieldEvidenceResponse])
def get_inspection_evidence(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    _verify_inspection_access(inspection, current_user)
    evidence_list = db.query(EVCFieldEvidence).filter(
        EVCFieldEvidence.inspection_id == id
    ).order_by(EVCFieldEvidence.created_at.asc()).all()

    return [_serialize_evidence(e) for e in evidence_list]


@router.post("/inspections/{id}/finalize", response_model=EVCInspectionResponse)
def finalize_inspection_report(
    id: int,
    request: EVCReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inspector report submission.
    Statutory Safeguard: Moves application to EVC_COMPLETED without granting statutory approval.
    Competent Authority exclusively retains final decision order authority.
    """
    inspection = EVCWorkflowService.finalize_inspection_report(
        db=db,
        inspection_id=id,
        report_url=request.report_url,
        report_notes=request.report_notes,
        recommendation=request.recommendation,
        virtual_meeting_url=request.virtual_meeting_url,
        virtual_recording_url=request.virtual_recording_url,
        actor=current_user
    )
    return _serialize_inspection(inspection)


@router.get("/inspections/{id}", response_model=EVCInspectionResponse)
@router.get("/inspections/{id}/dossier", response_model=EVCInspectionResponse)
def get_evc_dossier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns full EVC dossier including panel assignments, COI assessments, check-in provenance,
    checklist evidence items, and final inspection recommendations.
    """
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    _verify_inspection_access(inspection, current_user)
    return _serialize_inspection(inspection)

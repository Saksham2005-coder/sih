from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
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


def _is_institution_user(user: Optional[User]) -> bool:
    if not user:
        return False
    user_roles = [r.role for r in user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)
    return not is_officer


def _serialize_panel_assignment(a: EVCPanelAssignment, current_user: Optional[User] = None) -> EVCPanelAssignmentResponse:
    expert = a.expert
    is_inst = _is_institution_user(current_user)
    return EVCPanelAssignmentResponse(
        id=a.id,
        inspection_id=a.inspection_id,
        expert_id=a.expert_id,
        expert_name=expert.name if expert else None,
        expert_email=None if is_inst else (expert.email if expert else None),
        expert_institution=expert.current_institution if expert else None,
        panel_role=a.panel_role,
        status=a.status,
        invited_at=a.invited_at,
        responded_at=a.responded_at,
        decline_reason=None if is_inst else a.decline_reason,
        coi_check_result=None if is_inst else a.coi_check_result,
        override_applied=a.override_applied,
        override_reason=None if is_inst else a.override_reason,
        created_at=a.created_at,
        updated_at=a.updated_at
    )


def _serialize_evidence(e: EVCFieldEvidence, current_user: Optional[User] = None) -> EVCFieldEvidenceResponse:
    is_inst = _is_institution_user(current_user)
    return EVCFieldEvidenceResponse(
        id=e.id,
        inspection_id=e.inspection_id,
        checklist_item_code=e.checklist_item_code,
        requirement_title=e.requirement_title,
        observation_notes=e.observation_notes,
        status=e.status,
        file_url=e.file_url,
        file_hash=None if is_inst else e.file_hash,
        file_name=e.file_name,
        file_size_bytes=e.file_size_bytes,
        evidence_type=e.evidence_type,
        captured_by_id=e.captured_by_id,
        captured_at=e.captured_at,
        latitude=None if is_inst else e.latitude,
        longitude=None if is_inst else e.longitude,
        location_accuracy_meters=None if is_inst else e.location_accuracy_meters,
        location_capture_source=None if is_inst else e.location_capture_source,
        location_permission_granted=e.location_permission_granted,
        created_at=e.created_at,
        updated_at=e.updated_at
    )


def _serialize_inspection(insp: EVCInspection, current_user: Optional[User] = None) -> EVCInspectionResponse:
    app = insp.application
    inst = app.institution if app else None
    is_inst = _is_institution_user(current_user)
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
        check_in_lat=None if is_inst else insp.check_in_lat,
        check_in_lon=None if is_inst else insp.check_in_lon,
        check_in_accuracy=None if is_inst else insp.check_in_accuracy,
        check_in_source=None if is_inst else insp.check_in_source,
        virtual_meeting_url=None if is_inst else insp.virtual_meeting_url,
        virtual_recording_url=None if is_inst else insp.virtual_recording_url,
        report_url=insp.report_url,
        report_notes=insp.report_notes,
        recommendation=insp.recommendation,
        completed_at=insp.completed_at,
        completed_by_id=insp.completed_by_id,
        created_at=insp.created_at,
        updated_at=insp.updated_at,
        panel_assignments=[_serialize_panel_assignment(a, current_user) for a in (insp.panel_assignments or [])],
        field_evidence=[_serialize_evidence(e, current_user) for e in (insp.field_evidence or [])]
    )


def _verify_inspection_access(
    inspection: EVCInspection,
    current_user: User,
    require_mutation: bool = False,
    is_report_submission: bool = False
):
    user_roles = [r.role for r in current_user.roles]
    app = inspection.application
    if not app:
        raise HTTPException(status_code=404, detail="Inspection application not found")
    inst = app.institution
    inst_region = (inst.region or "").strip() if inst else ""

    # 1. Institution Users: view only their institution's permitted inspection records
    if _is_institution_user(current_user):
        if not current_user.institution_id or app.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Unauthorized: Access denied to inspection outside institution")
        if require_mutation:
            raise HTTPException(status_code=403, detail="Unauthorized: Institution users cannot perform inspection operations")
        return

    # 2. System Administrators: retain infrastructure and read-only visibility;
    # NEVER automatic authority to submit inspection reports or issue statutory decisions.
    if "SYSTEM_ADMIN" in user_roles and not any(r in ["COMMITTEE_MEMBER", "EVC_COORDINATOR", "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
        if is_report_submission or require_mutation:
            raise HTTPException(
                status_code=403,
                detail="Access denied: System Administrators retain read-only infrastructure visibility and cannot submit inspection reports or mutate inspection evidence."
            )
        return

    # 3. Regional Officers: fail closed without a valid assigned region; cannot access or mutate inspections outside jurisdiction.
    if "REGIONAL_OFFICER" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
        if not current_user.region or not current_user.region.strip():
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer account has no assigned regional jurisdiction (fail-closed).")
        if inst_region and inst_region.lower() != current_user.region.strip().lower():
            raise HTTPException(status_code=403, detail=f"Unauthorized: Access denied to region '{inst_region}'. Outside your assigned region '{current_user.region}'.")
        return

    # 4. Committee Members: may access only inspections assigned to them through the relevant EVC panel assignment
    if "COMMITTEE_MEMBER" in user_roles and not any(r in ["BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN", "EVC_COORDINATOR", "REGIONAL_OFFICER"] for r in user_roles):
        active_assignments = [
            a for a in (inspection.panel_assignments or [])
            if a.status in ["INVITED", "ACCEPTED", "COMPLETED"]
        ]
        if active_assignments:
            is_assigned = any(
                a.expert and (a.expert.user_id == current_user.id or a.expert.email == current_user.email)
                for a in active_assignments
            ) or (inspection.convener_user_id == current_user.id or inspection.expert_user_id == current_user.id)
            if not is_assigned:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: Committee Member is not assigned to this inspection panel."
                )
        else:
            if inspection.convener_user_id or inspection.expert_user_id:
                if current_user.id not in [inspection.convener_user_id, inspection.expert_user_id]:
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: Committee Member is not assigned to this inspection panel."
                    )
        return

    # 5. EVC Coordinators: may access and manage only the inspection records permitted by their scheduling authority and jurisdiction
    if "EVC_COORDINATOR" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
        if current_user.region and current_user.region.strip() and current_user.region.strip() != "ALL_INDIA":
            if inst_region and inst_region.lower() != current_user.region.strip().lower():
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: Case is registered under '{inst_region}' Region, outside your scheduling jurisdiction '{current_user.region}'."
                )
        return

    # 6. Bureau Officers and Competent Authority retain authorized national access
    if any(r in ["BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
        return


def _mask_expert_profile(expert: EVCExpert, current_user: User) -> dict:
    user_roles = [r.role for r in current_user.roles]
    is_privileged = any(r in ["SYSTEM_ADMIN", "EVC_COORDINATOR"] for r in user_roles)

    email = expert.email
    phone = expert.phone
    declared_conflicts = expert.declared_conflicts or []

    if not is_privileged:
        # Mask email: e.g. "amitav.roy@iitb.ac.in" -> "a***y@iitb.ac.in"
        if email and "@" in email:
            parts = email.split("@")
            user_part = parts[0]
            domain_part = parts[1]
            if len(user_part) > 2:
                masked_user = f"{user_part[0]}***{user_part[-1]}"
            else:
                masked_user = f"{user_part[0]}***"
            email = f"{masked_user}@{domain_part}"
        elif email:
            email = "e***@masked.in"

        # Mask phone
        if phone:
            digits = "".join(c for c in phone if c.isdigit())
            last4 = digits[-4:] if len(digits) >= 4 else "0000"
            phone = f"+91-XXXXX-{last4}"

        # Sanitize declared conflict reasons
        sanitized_conflicts = []
        for dc in declared_conflicts:
            sanitized_conflicts.append({
                "institution_id": dc.get("institution_id"),
                "institution_name": dc.get("institution_name"),
                "reason": "Declared personal / institutional conflict (confidential officer record)"
            })
        declared_conflicts = sanitized_conflicts

    return {
        "id": expert.id,
        "user_id": expert.user_id,
        "name": expert.name,
        "email": email,
        "phone": phone,
        "designation": expert.designation,
        "expertise_categories": expert.expertise_categories or [],
        "specializations": expert.specializations or [],
        "current_institution": expert.current_institution,
        "institution_id": expert.institution_id,
        "parent_organization": expert.parent_organization,
        "district": expert.district,
        "region": expert.region,
        "is_active": expert.is_active,
        "availability_status": expert.availability_status,
        "declared_conflicts": declared_conflicts,
        "prior_inspections": expert.prior_inspections or [],
        "created_at": expert.created_at,
        "updated_at": expert.updated_at
    }


# ==========================================
# QUEUE & SCHEDULE (BACKWARD COMPATIBLE)
# ==========================================

@router.get("/queue", response_model=List[EVCInspectionResponse])
def get_evc_queue(
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EVCInspection).join(
        Application, EVCInspection.application_id == Application.id
    ).join(
        Institution, Application.institution_id == Institution.id
    )

    user_roles = [r.role for r in current_user.roles]

    if _is_institution_user(current_user):
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    else:
        # Committee Members: view inspections assigned to them through active panel assignments, or unassigned records
        if "COMMITTEE_MEMBER" in user_roles and not any(r in ["BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN", "EVC_COORDINATOR", "REGIONAL_OFFICER"] for r in user_roles):
            query = query.outerjoin(EVCInspection.panel_assignments).outerjoin(EVCPanelAssignment.expert).filter(
                or_(
                    and_(EVCExpert.user_id == current_user.id, EVCPanelAssignment.status.in_(["INVITED", "ACCEPTED", "COMPLETED", "PROPOSED"])),
                    EVCInspection.convener_user_id == current_user.id,
                    EVCInspection.expert_user_id == current_user.id,
                    and_(EVCInspection.convener_user_id.is_(None), EVCInspection.expert_user_id.is_(None), ~EVCInspection.panel_assignments.any())
                )
            )
        # Regional Officers: fail closed without assigned region; strictly scoped to assigned region
        elif "REGIONAL_OFFICER" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
            if not current_user.region or not current_user.region.strip():
                raise HTTPException(status_code=403, detail="Access denied: Regional Officer account has no assigned regional jurisdiction (fail-closed).")
            if region and region.strip().lower() != current_user.region.strip().lower():
                raise HTTPException(status_code=403, detail=f"Access denied: Regional Officer assigned to '{current_user.region}' cannot query region '{region}'.")
            query = query.filter(Institution.region == current_user.region)
        # EVC Coordinators: check jurisdiction if regionally assigned
        elif "EVC_COORDINATOR" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
            if current_user.region and current_user.region.strip() and current_user.region.strip() != "ALL_INDIA":
                if region and region.strip().lower() != current_user.region.strip().lower():
                    raise HTTPException(status_code=403, detail=f"Access denied: Region '{region}' outside your scheduling jurisdiction '{current_user.region}'.")
                query = query.filter(Institution.region == current_user.region)
            elif region:
                query = query.filter(Institution.region == region)
        elif region:
            query = query.filter(Institution.region == region)

    inspections = query.order_by(EVCInspection.scheduled_date.asc().nullslast()).all()
    return [_serialize_inspection(insp, current_user) for insp in inspections]


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
    return _serialize_inspection(inspection, current_user)


@router.post("/{id}/submit-report", response_model=EVCInspectionResponse)
@router.post("/inspections/{id}/report", response_model=EVCInspectionResponse)
def submit_evc_report(
    id: int,
    request: EVCReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC inspection not found")

    _verify_inspection_access(inspection, current_user, require_mutation=True, is_report_submission=True)

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

    return _serialize_inspection(inspection, current_user)


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
    Restricted to authorized officers. Regional Officers fail closed if region missing or foreign region requested.
    """
    user_roles = [r.role for r in current_user.roles]
    allowed_roles = {"EVC_COORDINATOR", "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"}
    if not any(r in allowed_roles for r in user_roles):
        raise HTTPException(status_code=403, detail="Unauthorized: Expert registry view restricted to authorized officers")

    query = db.query(EVCExpert)

    # Scoping: Regional officer scoping
    if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if not current_user.region or not current_user.region.strip():
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer account has no assigned regional jurisdiction (fail-closed).")
        # Regional Officer must NEVER broaden their region through query parameter
        if region and region.strip().lower() != current_user.region.strip().lower():
            raise HTTPException(status_code=403, detail=f"Access denied: Regional Officers cannot query expert profiles outside their assigned region '{current_user.region}'.")
        query = query.filter(or_(EVCExpert.region == current_user.region, EVCExpert.region == "ALL_INDIA"))
    elif region:
        query = query.filter(EVCExpert.region == region)

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
    return [_mask_expert_profile(exp, current_user) for exp in experts]


@router.get("/experts/{id}", response_model=EVCExpertResponse)
def get_evc_expert_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role for r in current_user.roles]
    allowed_roles = {"EVC_COORDINATOR", "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"}
    if not any(r in allowed_roles for r in user_roles):
        raise HTTPException(status_code=403, detail="Unauthorized: Expert profile view restricted to authorized officers")

    expert = db.query(EVCExpert).filter(EVCExpert.id == id).first()
    if not expert:
        raise HTTPException(status_code=404, detail="Expert profile not found")

    # Scoping for Regional Officer
    if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if not current_user.region or not current_user.region.strip():
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer account has no assigned regional jurisdiction (fail-closed).")
        if expert.region and expert.region != "ALL_INDIA" and expert.region.strip().lower() != current_user.region.strip().lower():
            raise HTTPException(status_code=403, detail=f"Access denied: Expert #{id} belongs to '{expert.region}' region outside your jurisdiction '{current_user.region}'.")

    return _mask_expert_profile(expert, current_user)


@router.post("/coi-check", response_model=COICheckResponse)
def check_conflict_of_interest(
    request: COICheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes explainable conflict-of-interest check against the specified institution application.
    Enforces server-side role and regional permission boundaries.
    """
    user_roles = [r.role for r in current_user.roles]
    allowed_roles = {"EVC_COORDINATOR", "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"}
    if not any(r in allowed_roles for r in user_roles):
        raise HTTPException(status_code=403, detail="Unauthorized: Conflict-of-interest evaluation restricted to authorized officers")

    expert = db.query(EVCExpert).filter(EVCExpert.id == request.expert_id).first()
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert #{request.expert_id} not found")

    application = db.query(Application).filter(Application.id == request.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application #{request.application_id} not found")

    # Regional Officer Scoping
    if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if not current_user.region or not current_user.region.strip():
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer account has no assigned regional jurisdiction (fail-closed).")
        inst_region = application.institution.region if (application and application.institution) else None
        if inst_region and inst_region.strip().lower() != current_user.region.strip().lower():
            raise HTTPException(status_code=403, detail=f"Access denied: Case is registered under '{inst_region}' Region, which is outside your assigned region '{current_user.region}'.")
        if expert.region and expert.region != "ALL_INDIA" and expert.region.strip().lower() != current_user.region.strip().lower():
            raise HTTPException(status_code=403, detail=f"Access denied: Expert belongs to '{expert.region}' region, which is outside your assigned region '{current_user.region}'.")

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
    inspection = db.query(EVCInspection).filter(EVCInspection.id == request.inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection record not found")

    _verify_inspection_access(inspection, current_user, require_mutation=True)

    assignment = EVCWorkflowService.propose_panel_assignment(
        db=db,
        inspection_id=request.inspection_id,
        expert_id=request.expert_id,
        panel_role=request.panel_role,
        actor=current_user,
        override_reason=request.override_reason
    )
    return _serialize_panel_assignment(assignment, current_user)


@router.post("/assignments/{id}/invite", response_model=EVCPanelAssignmentResponse)
def invite_panel_expert(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dispatches formal invitation notice to proposed expert via notification outbox.
    """
    assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Panel assignment not found")

    if assignment.inspection:
        _verify_inspection_access(assignment.inspection, current_user, require_mutation=True)

    assignment = EVCWorkflowService.invite_expert(
        db=db,
        assignment_id=id,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment, current_user)


@router.post("/assignments/{id}/accept", response_model=EVCPanelAssignmentResponse)
def accept_panel_invitation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks invitation ACCEPTED. When both Convener and Expert Member accept, transitions inspection to SCHEDULED.
    Only the invited expert linked to this assignment can accept.
    """
    assignment = EVCWorkflowService.accept_invitation(
        db=db,
        assignment_id=id,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment, current_user)


@router.post("/assignments/{id}/decline", response_model=EVCPanelAssignmentResponse)
def decline_panel_invitation(
    id: int,
    request: EVCInvitationDeclineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Declines invitation with reason. Transitions inspection to REASSIGNMENT_REQUIRED.
    Only the invited expert linked to this assignment can decline.
    """
    assignment = EVCWorkflowService.decline_invitation(
        db=db,
        assignment_id=id,
        reason=request.reason,
        actor=current_user
    )
    return _serialize_panel_assignment(assignment, current_user)


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
    assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Original panel assignment not found")

    if assignment.inspection:
        _verify_inspection_access(assignment.inspection, current_user, require_mutation=True)

    new_assignment = EVCWorkflowService.reassign_panel_member(
        db=db,
        old_assignment_id=id,
        new_expert_id=request.new_expert_id,
        actor=current_user,
        override_reason=request.override_reason
    )
    return _serialize_panel_assignment(new_assignment, current_user)


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
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    _verify_inspection_access(inspection, current_user, require_mutation=True)

    inspection = EVCWorkflowService.check_in_inspection(
        db=db,
        inspection_id=id,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy,
        source=request.source,
        actor=current_user
    )
    return _serialize_inspection(inspection, current_user)


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
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    _verify_inspection_access(inspection, current_user, require_mutation=True)

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
    return _serialize_evidence(evidence, current_user)


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

    return [_serialize_evidence(e, current_user) for e in evidence_list]


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
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    _verify_inspection_access(inspection, current_user, require_mutation=True, is_report_submission=True)

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
    return _serialize_inspection(inspection, current_user)


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
    return _serialize_inspection(inspection, current_user)

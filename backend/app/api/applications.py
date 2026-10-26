import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.institution import Institution
from app.models.evc import EVCInspection
from app.models.alert import AlertEscalation
from app.models.audit import AuditEvent
from app.schemas.application import (
    ApplicationResponse, ApplicationDetailResponse, ApplicationCreateRequest,
    ApplicationTransitionRequest, DeficiencyCreateRequest, DeficiencyCureRequest,
    DeficiencyResponse, ApplicationLifecycleResponse, ApplicationAuditTrailItem
)
from app.services.workflow_engine import execute_transition, get_allowed_transitions
from app.services.priority_service import calculate_priority
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    stage: Optional[str] = None,
    application_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).join(Institution, Application.institution_id == Institution.id)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    # Multi-tenant isolation: Institution users can only query their own records
    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        # Regional officer sees applications in their assigned region
        query = query.filter(Institution.region == current_user.region)
    elif "EVC_COORDINATOR" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if current_user.region:
            query = query.filter(Institution.region == current_user.region)
        query = query.filter(or_(
            Application.evc_required == True,
            Application.current_stage.in_(["AWAITING_EVC_SCHEDULE", "EVC_SCHEDULED", "EVC_COMPLETED"]),
            Application.workflow_template_code.in_(["NEW_INSTITUTION", "SCRUTINY_EVC", "EVC_SAC_SHC", "ONLY_EVC"])
        ))
    elif "COMMITTEE_MEMBER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        assigned_evc_app_ids = db.query(EVCInspection.application_id).filter(
            or_(
                EVCInspection.convener_user_id == current_user.id,
                EVCInspection.expert_user_id == current_user.id,
                EVCInspection.completed_by_id == current_user.id
            )
        )
        query = query.filter(or_(
            Application.current_stage == "AWAITING_SAC_CAC_REVIEW",
            Application.id.in_(assigned_evc_app_ids)
        ))

    if stage:
        query = query.filter(Application.current_stage == stage)
    if application_type:
        query = query.filter(Application.application_type == application_type)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Application.application_number.ilike(search_filter)) |
            (Institution.name.ilike(search_filter)) |
            (Institution.code.ilike(search_filter))
        )

    apps = query.order_by(Application.priority_score.desc(), Application.updated_at.desc()).all()
    
    results = []
    for app in apps:
        open_defs = db.query(Deficiency).filter(Deficiency.application_id == app.id, Deficiency.status == "OPEN").count()
        score, factors = calculate_priority(app, db)
        app.priority_score = score
        results.append(ApplicationResponse(
            id=app.id,
            application_number=app.application_number,
            institution_id=app.institution_id,
            institution_name=app.institution.name,
            region=app.institution.region,
            academic_year=app.academic_year,
            application_type=app.application_type,
            workflow_template_code=app.workflow_template_code,
            current_stage=app.current_stage,
            scrutiny_officer_id=app.scrutiny_officer_id,
            priority_score=score,
            priority_factors=factors,
            version=app.version,
            evc_required=app.evc_required,
            submitted_at=app.submitted_at,
            approved_at=app.approved_at,
            rejected_at=app.rejected_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
            open_deficiencies_count=open_defs
        ))
    return results

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    request: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN"]))
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="User is not associated with an institution.")

    # Generate sequential application number
    now = datetime.now(timezone.utc)
    count = db.query(Application).count() + 101
    
    template_code = request.workflow_template_code or request.application_type
    requires_evc = request.evc_required if request.evc_required is not None else (
        template_code in ["NEW_INSTITUTION", "SCRUTINY_EVC", "EVC_SAC_SHC", "ONLY_EVC"]
    )
    
    prefix = "EOA"
    if template_code in ["NEW_INSTITUTION", "SCRUTINY_EVC"]:
        prefix = "NEW"
    elif template_code == "EVC_SAC_SHC":
        prefix = "EXP"
    elif template_code == "ONLY_EVC":
        prefix = "INSP"

    app_num = f"AICTE-2026-{prefix}-{count:05d}"

    new_app = Application(
        application_number=app_num,
        institution_id=current_user.institution_id,
        academic_year=request.academic_year,
        application_type=request.application_type,
        workflow_template_code=template_code,
        evc_required=requires_evc,
        current_stage="SUBMITTED",
        submitted_at=now,
        priority_score=30
    )
    db.add(new_app)
    db.flush()

    # Add initial stage timeline
    stage_event = ApplicationStage(
        application_id=new_app.id,
        from_stage="DRAFT",
        to_stage="SUBMITTED",
        actor_id=current_user.id,
        actor_role="INSTITUTION_ADMIN",
        actor_name=current_user.full_name,
        remarks="Regulatory application filed with prescribed fee and statutory undertakings."
    )
    db.add(stage_event)

    log_audit_event(
        db=db,
        action="APPLICATION_CREATED",
        entity_type="APPLICATION",
        entity_id=new_app.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="INSTITUTION_ADMIN",
        details={"application_number": app_num, "type": request.application_type, "template": template_code}
    )

    db.commit()
    db.refresh(new_app)

    score, factors = calculate_priority(new_app, db)
    return ApplicationResponse(
        id=new_app.id,
        application_number=new_app.application_number,
        institution_id=new_app.institution_id,
        institution_name=new_app.institution.name,
        region=new_app.institution.region,
        academic_year=new_app.academic_year,
        application_type=new_app.application_type,
        workflow_template_code=new_app.workflow_template_code,
        current_stage=new_app.current_stage,
        scrutiny_officer_id=new_app.scrutiny_officer_id,
        priority_score=score,
        priority_factors=factors,
        version=new_app.version,
        evc_required=new_app.evc_required,
        submitted_at=new_app.submitted_at,
        created_at=new_app.created_at,
        updated_at=new_app.updated_at,
        open_deficiencies_count=0
    )

@router.get("/{id}", response_model=ApplicationDetailResponse)
def get_application_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Isolation check
    verify_institution_access(app.institution_id, current_user)
    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    score, factors = calculate_priority(app, db)
    open_defs = db.query(Deficiency).filter(Deficiency.application_id == app.id, Deficiency.status == "OPEN").count()

    return ApplicationDetailResponse(
        id=app.id,
        application_number=app.application_number,
        institution_id=app.institution_id,
        institution_name=app.institution.name,
        region=app.institution.region,
        academic_year=app.academic_year,
        application_type=app.application_type,
        workflow_template_code=app.workflow_template_code,
        current_stage=app.current_stage,
        scrutiny_officer_id=app.scrutiny_officer_id,
        priority_score=score,
        priority_factors=factors,
        version=app.version,
        evc_required=app.evc_required,
        submitted_at=app.submitted_at,
        approved_at=app.approved_at,
        rejected_at=app.rejected_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        open_deficiencies_count=open_defs,
        stages=app.stages,
        deficiencies=app.deficiencies
    )

@router.post("/{id}/transition", response_model=ApplicationDetailResponse)
def transition_application_stage(
    id: int,
    request: ApplicationTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)
    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    updated_app = execute_transition(
        db=db,
        application=app,
        to_stage=request.to_stage,
        actor=current_user,
        remarks=request.remarks,
        expected_version=request.expected_version
    )

    return get_application_detail(id=updated_app.id, db=db, current_user=current_user)

@router.post("/{id}/deficiencies", response_model=DeficiencyResponse, status_code=status.HTTP_201_CREATED)
def issue_deficiency(
    id: int,
    request: DeficiencyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    deficiency = Deficiency(
        application_id=app.id,
        category=request.category,
        description=request.description,
        required_document=request.required_document,
        status="OPEN"
    )
    db.add(deficiency)
    
    # Automatically move application to DEFICIENCY_COMMUNICATED if currently under scrutiny
    if app.current_stage == "UNDER_SCRUTINY":
        execute_transition(
            db=db,
            application=app,
            to_stage="DEFICIENCY_COMMUNICATED",
            actor=current_user,
            remarks=f"Deficiency issued in category '{request.category}': {request.description}"
        )
    else:
        db.commit()

    db.refresh(deficiency)
    return deficiency

@router.post("/{id}/cure-deficiency/{deficiency_id}", response_model=DeficiencyResponse)
@router.post("/{id}/deficiencies/{deficiency_id}/cure", response_model=DeficiencyResponse)
def cure_deficiency(
    id: int,
    deficiency_id: int,
    request: DeficiencyCureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)

    deficiency = db.query(Deficiency).filter(
        Deficiency.id == deficiency_id,
        Deficiency.application_id == app.id
    ).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency item not found")

    deficiency.status = "CURED"
    deficiency.cure_remarks = request.cure_remarks
    if request.cure_document_url:
        deficiency.cure_document_url = request.cure_document_url
    deficiency.cured_at = datetime.now(timezone.utc)

    actor_role = current_user.roles[0].role if current_user.roles else "INSTITUTION_ADMIN"
    log_audit_event(
        db=db,
        action="DEFICIENCY_CURE_SUBMITTED",
        entity_type="DEFICIENCY",
        entity_id=deficiency.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"application_id": app.id, "remarks": request.cure_remarks}
    )

    db.commit()
    db.refresh(deficiency)
    return deficiency

@router.post("/{id}/resolve-deficiency/{deficiency_id}", response_model=DeficiencyResponse)
@router.post("/{id}/deficiencies/{deficiency_id}/resolve", response_model=DeficiencyResponse)
def resolve_deficiency(
    id: int,
    deficiency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    deficiency = db.query(Deficiency).filter(
        Deficiency.id == deficiency_id,
        Deficiency.application_id == app.id
    ).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency item not found")

    deficiency.status = "CURED"
    deficiency.resolved_by_officer_id = current_user.id

    actor_role = current_user.roles[0].role if current_user.roles else "REGIONAL_OFFICER"
    log_audit_event(
        db=db,
        action="DEFICIENCY_RESOLVED",
        entity_type="DEFICIENCY",
        entity_id=deficiency.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"application_id": app.id, "deficiency_id": deficiency.id}
    )

    db.commit()
    db.refresh(deficiency)
    return deficiency

@router.get("/{id}/case-brief")
def get_case_brief(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deterministic Case Brief Assistant summarizing recorded application milestones and evidence"""
    from app.services.case_brief_service import CaseBriefService
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)
    
    # Regional Officer access check
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if app.institution.region != current_user.region:
            raise HTTPException(status_code=403, detail="Forbidden: Application outside assigned regional jurisdiction")

    return CaseBriefService.generate_case_brief(app.id, db)


@router.get("/{id}/audit-trail", response_model=ApplicationLifecycleResponse)
@router.get("/{id}/lifecycle", response_model=ApplicationLifecycleResponse)
def get_application_lifecycle_audit_trail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exposes complete, chronological regulatory lifecycle and audit trail for an application.
    Answers:
    - Who performed this action?
    - Which record changed?
    - What was the previous and resulting state?
    - Why was the action taken?
    - Which deadline, alert or rule version applied?
    - Was the action accepted, rejected, retried or acknowledged?
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)
    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    timeline: List[ApplicationAuditTrailItem] = []

    # 1. Application submission event
    timeline.append(ApplicationAuditTrailItem(
        id=app.id,
        timestamp=app.submitted_at or app.created_at,
        event_type="APPLICATION_FILED",
        actor_name=app.institution.name if app.institution else "Institution Admin",
        actor_role="INSTITUTION_ADMIN",
        actor_id=None,
        previous_state="DRAFT",
        resulting_state=app.stages[0].to_stage if app.stages else "SUBMITTED",
        reason_or_remarks=f"Application {app.application_number} filed for {app.academic_year} ({app.application_type}). Route template: {app.workflow_template_code}.",
        rule_or_version_applied="AICTE Approval Process Handbook (APH) Chapter I & II",
        outcome_status="SUBMITTED",
        entity_type="APPLICATION",
        entity_id=app.id,
        metadata={"application_type": app.application_type, "evc_required": app.evc_required}
    ))

    # 2. Stage transitions
    for stg in app.stages:
        outcome = "ADVANCED"
        if stg.to_stage == "DEFICIENCY_COMMUNICATED":
            outcome = "RETURNED_FOR_DEFICIENCY"
        elif stg.to_stage == "APPROVED":
            outcome = "APPROVED"
        elif stg.to_stage == "REJECTED":
            outcome = "REJECTED"
        elif stg.to_stage == "RESUBMITTED":
            outcome = "RESUBMITTED"
        elif stg.to_stage == "CLOSED":
            outcome = "CLOSED"

        timeline.append(ApplicationAuditTrailItem(
            id=stg.id,
            timestamp=stg.created_at,
            event_type="STAGE_TRANSITION",
            actor_name=stg.actor_name or "System / Officer",
            actor_role=stg.actor_role or "OFFICER",
            actor_id=stg.actor_id,
            previous_state=stg.from_stage or "SUBMITTED",
            resulting_state=stg.to_stage,
            reason_or_remarks=stg.remarks or f"Workflow progressed to {stg.to_stage.replace('_', ' ')}.",
            rule_or_version_applied=f"Workflow State Machine (Version {app.version})",
            outcome_status=outcome,
            entity_type="APPLICATION_STAGE",
            entity_id=stg.id,
            metadata={"from_stage": stg.from_stage, "to_stage": stg.to_stage}
        ))

    # 3. Itemized Deficiencies and Cures
    for d in app.deficiencies:
        # Issuance
        timeline.append(ApplicationAuditTrailItem(
            id=d.id,
            timestamp=d.created_at,
            event_type="DEFICIENCY_COMMUNICATED",
            actor_name="Scrutiny Committee / Regional Officer",
            actor_role="REGIONAL_OFFICER",
            actor_id=None,
            previous_state="UNDER_SCRUTINY",
            resulting_state="DEFICIENCY_COMMUNICATED",
            reason_or_remarks=f"[{d.category}] {d.description}" + (f" (Required Document: {d.required_document})" if d.required_document else ""),
            rule_or_version_applied="APH Deficiency Rectification Norms (SLA: 10 Days)",
            outcome_status="DEFICIENT",
            entity_type="DEFICIENCY",
            entity_id=d.id,
            metadata={"category": d.category, "required_document": d.required_document}
        ))

        # Cure submission
        if d.cured_at:
            timeline.append(ApplicationAuditTrailItem(
                id=d.id,
                timestamp=d.cured_at,
                event_type="DEFICIENCY_CURED",
                actor_name=app.institution.name if app.institution else "Institution User",
                actor_role="INSTITUTION_ADMIN",
                actor_id=None,
                previous_state="DEFICIENCY_COMMUNICATED",
                resulting_state="CURED",
                reason_or_remarks=d.cure_remarks or "Rectification evidence document uploaded by institution.",
                rule_or_version_applied="Institutional Cure Compliance Protocol",
                outcome_status="CURED",
                entity_type="DEFICIENCY",
                entity_id=d.id,
                metadata={"cure_document_url": d.cure_document_url}
            ))

        # Resolution
        if d.resolved_by_officer_id:
            resolving_user = db.query(User).filter(User.id == d.resolved_by_officer_id).first()
            timeline.append(ApplicationAuditTrailItem(
                id=d.id,
                timestamp=d.cured_at or d.created_at,
                event_type="DEFICIENCY_RESOLVED",
                actor_name=resolving_user.full_name if resolving_user else "Authorized Officer",
                actor_role="REGIONAL_OFFICER",
                actor_id=d.resolved_by_officer_id,
                previous_state="CURED",
                resulting_state="RESOLVED",
                reason_or_remarks=f"Deficiency in {d.category} verified and marked resolved upon scrutiny review.",
                rule_or_version_applied="Officer Deficiency Verification Norms",
                outcome_status="RESOLVED",
                entity_type="DEFICIENCY",
                entity_id=d.id,
                metadata={"resolved_by": resolving_user.full_name if resolving_user else "Officer"}
            ))

    # 4. EVC Inspections
    for insp in app.evc_inspections:
        if insp.scheduled_date:
            coord = db.query(User).filter(User.id == insp.coordinator_id).first()
            timeline.append(ApplicationAuditTrailItem(
                id=insp.id,
                timestamp=insp.created_at,
                event_type="EVC_SCHEDULED",
                actor_name=coord.full_name if coord else "EVC Coordinator",
                actor_role="EVC_COORDINATOR",
                actor_id=insp.coordinator_id,
                previous_state="AWAITING_EVC_SCHEDULE",
                resulting_state="EVC_SCHEDULED",
                reason_or_remarks=f"Inspection panel constituted: Convener '{insp.convener_name}', Subject Expert '{insp.expert_member_name}'. Visit scheduled for {insp.scheduled_date.strftime('%d %b %Y, %H:%M UTC')}.",
                rule_or_version_applied="APH Chapter III Physical/Virtual EVC Regulations",
                outcome_status="SCHEDULED",
                entity_type="EVC_INSPECTION",
                entity_id=insp.id,
                metadata={"inspection_type": insp.inspection_type, "convener": insp.convener_name, "expert": insp.expert_member_name}
            ))

        if insp.status in ("REPORT_SUBMITTED", "RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"):
            timeline.append(ApplicationAuditTrailItem(
                id=insp.id,
                timestamp=insp.completed_at or insp.updated_at,
                event_type="EVC_REPORTED",
                actor_name=f"EVC Panel ({insp.convener_name})",
                actor_role="COMMITTEE_MEMBER",
                actor_id=insp.completed_by_id,
                previous_state="EVC_SCHEDULED",
                resulting_state="EVC_COMPLETED",
                reason_or_remarks=f"Panel Recommendation: {insp.recommendation.replace('_', ' ')}. Observations: {insp.report_notes or 'Inspection findings recorded.'}",
                rule_or_version_applied="Expert Visit Report & Panel Assessment Standard",
                outcome_status=insp.recommendation,
                entity_type="EVC_INSPECTION",
                entity_id=insp.id,
                metadata={"report_url": insp.report_url, "recommendation": insp.recommendation}
            ))

    # 5. Escalations and Acknowledgements
    escalations = db.query(AlertEscalation).filter(
        AlertEscalation.entity_type == "APPLICATION",
        AlertEscalation.entity_id == app.id
    ).all()
    for esc in escalations:
        timeline.append(ApplicationAuditTrailItem(
            id=esc.id,
            timestamp=esc.created_at,
            event_type="ESCALATION_TRIGGERED",
            actor_name="ReguFlow Automated Deadline Daemon",
            actor_role="SYSTEM_ADMIN",
            actor_id=None,
            previous_state="PENDING_PROCESSING",
            resulting_state=esc.escalation_level,
            reason_or_remarks=f"Automated Alert Escalation [{esc.escalation_level}]: Triggered by '{esc.trigger_type}' ({esc.threshold_days} days threshold) for recipient {esc.recipient_role}.",
            rule_or_version_applied=f"Rule Studio SLA Policy {esc.rule_code or 'APH-SLA-01'} v{esc.rule_version or '1.0.0'}",
            outcome_status="TRIGGERED",
            entity_type="ALERT_ESCALATION",
            entity_id=esc.id,
            metadata={"trigger_type": esc.trigger_type, "threshold_days": esc.threshold_days, "level": esc.escalation_level}
        ))
        if esc.acknowledged_at:
            ack_user = db.query(User).filter(User.id == esc.acknowledged_by_id).first() if esc.acknowledged_by_id else None
            timeline.append(ApplicationAuditTrailItem(
                id=esc.id,
                timestamp=esc.acknowledged_at,
                event_type="ESCALATION_ACKNOWLEDGED",
                actor_name=ack_user.full_name if ack_user else "Authorized Officer",
                actor_role=ack_user.roles[0].role if (ack_user and ack_user.roles) else "OFFICER",
                actor_id=esc.acknowledged_by_id,
                previous_state=esc.escalation_level,
                resulting_state="ACKNOWLEDGED",
                reason_or_remarks=f"Official acknowledgement: {esc.resolved_reason or 'Officer reviewed alert and scheduled hearing.'}",
                rule_or_version_applied="Officer Accountability & Escalation Acknowledgement SLA",
                outcome_status="ACKNOWLEDGED",
                entity_type="ALERT_ESCALATION",
                entity_id=esc.id,
                metadata={"acknowledged_by": ack_user.full_name if ack_user else "Officer"}
            ))

    # 6. Audit Events for statutory orders
    audit_events = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "APPLICATION",
        AuditEvent.entity_id == app.id,
        AuditEvent.action.in_(["STAGE_TRANSITION", "APPLICATION_CREATED", "STATUTORY_APPROVAL_GRANTED", "STATUTORY_REJECTION_ISSUED"])
    ).all()
    for ev in audit_events:
        if ev.action in ("STATUTORY_APPROVAL_GRANTED", "STATUTORY_REJECTION_ISSUED"):
            timeline.append(ApplicationAuditTrailItem(
                id=ev.id,
                timestamp=ev.created_at,
                event_type="STATUTORY_DECISION",
                actor_name=ev.actor_name,
                actor_role=ev.actor_role,
                actor_id=ev.actor_id,
                previous_state="AWAITING_COMPETENT_AUTHORITY",
                resulting_state=app.current_stage,
                reason_or_remarks=f"Official Competent Authority Decision Order: {ev.details or ''}",
                rule_or_version_applied="AICTE Act Section 10/11 Statutory Decision Authority",
                outcome_status=app.current_stage,
                entity_type="AUDIT_EVENT",
                entity_id=ev.id,
                metadata={"ip_address": ev.ip_address}
            ))

    # Sort chronological
    timeline.sort(key=lambda x: x.timestamp)

    return ApplicationLifecycleResponse(
        application_id=app.id,
        application_number=app.application_number,
        institution_name=app.institution.name if app.institution else "Apex Institute",
        region=app.institution.region if app.institution else "Western",
        current_stage=app.current_stage,
        academic_year=app.academic_year,
        workflow_template_code=app.workflow_template_code,
        version=app.version,
        timeline=timeline
    )

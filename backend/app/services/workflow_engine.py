from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.evc import EVCInspection
from app.models.alert import Notification
from app.models.user import User
from app.core.rbac import (
    check_institution_scope,
    check_regional_scope,
    REGIONAL_OFFICER,
    BUREAU_OFFICER,
    COMPETENT_AUTHORITY,
    SYSTEM_ADMIN,
    INSTITUTION_ADMIN,
    COMPLIANCE_OFFICER,
    COMMITTEE_MEMBER,
    EVC_COORDINATOR
)
from app.services.audit_service import log_audit_event

ALLOWED_TRANSITIONS: Dict[str, List[Tuple[str, List[str]]]] = {
    "DRAFT": [
        ("SUBMITTED", [INSTITUTION_ADMIN])
    ],
    "SUBMITTED": [
        ("UNDER_SCRUTINY", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_EVC_SCHEDULE", [REGIONAL_OFFICER, BUREAU_OFFICER])
    ],
    "UNDER_SCRUTINY": [
        ("DEFICIENCY_COMMUNICATED", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("SCRUTINY_COMPLETED", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_EVC_SCHEDULE", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_COMPETENT_AUTHORITY", [REGIONAL_OFFICER, BUREAU_OFFICER]),
    ],
    "DEFICIENCY_COMMUNICATED": [
        ("RESUBMITTED", [INSTITUTION_ADMIN, COMPLIANCE_OFFICER])
    ],
    "RESUBMITTED": [
        ("UNDER_SCRUTINY", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_SAC_CAC_REVIEW", [COMMITTEE_MEMBER, BUREAU_OFFICER]),
        ("AWAITING_COMPETENT_AUTHORITY", [COMPETENT_AUTHORITY, BUREAU_OFFICER])
    ],
    "SCRUTINY_COMPLETED": [
        ("AWAITING_EVC_SCHEDULE", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_SAC_CAC_REVIEW", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_COMPETENT_AUTHORITY", [REGIONAL_OFFICER, BUREAU_OFFICER]),
    ],
    "AWAITING_EVC_SCHEDULE": [
        ("EVC_SCHEDULED", [EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER])
    ],
    "EVC_SCHEDULED": [
        ("EVC_COMPLETED", [EVC_COORDINATOR, COMMITTEE_MEMBER])
    ],
    "EVC_COMPLETED": [
        ("AWAITING_SAC_CAC_REVIEW", [REGIONAL_OFFICER, BUREAU_OFFICER]),
        ("AWAITING_COMPETENT_AUTHORITY", [REGIONAL_OFFICER, BUREAU_OFFICER]),
    ],
    "AWAITING_SAC_CAC_REVIEW": [
        ("AWAITING_COMPETENT_AUTHORITY", [COMMITTEE_MEMBER, BUREAU_OFFICER]),
        ("DEFICIENCY_COMMUNICATED", [COMMITTEE_MEMBER, BUREAU_OFFICER])
    ],
    "AWAITING_COMPETENT_AUTHORITY": [
        ("APPROVED", [COMPETENT_AUTHORITY]),
        ("REJECTED", [COMPETENT_AUTHORITY]),
        ("DEFICIENCY_COMMUNICATED", [COMPETENT_AUTHORITY])
    ],
}

# Terminal or administrative closure allowed from any active stage
ADMIN_CLOSURE_ALLOWED_ROLES = [COMPETENT_AUTHORITY, SYSTEM_ADMIN]

TRANSITIONS_REQUIRING_REASONS = {
    "DEFICIENCY_COMMUNICATED",
    "REJECTED",
    "CLOSED"
}

def get_allowed_transitions(current_stage: str, user_roles: List[str]) -> List[str]:
    transitions = ALLOWED_TRANSITIONS.get(current_stage, [])
    allowed = []
    for to_stage, permitted_roles in transitions:
        if any(r in permitted_roles for r in user_roles):
            allowed.append(to_stage)
    if any(r in ADMIN_CLOSURE_ALLOWED_ROLES for r in user_roles) and current_stage not in ["APPROVED", "REJECTED", "CLOSED"]:
        allowed.append("CLOSED")
    return allowed

def execute_transition(
    db: Session,
    application: Application,
    to_stage: str,
    actor: User,
    remarks: Optional[str] = None,
    expected_version: Optional[int] = None
) -> Application:
    user_roles = [r.role for r in actor.roles]
    from_stage = application.current_stage

    # 1. Optimistic Concurrency Control (Version Check)
    if expected_version is not None:
        if application.version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Application state has changed (current version: {application.version}, expected: {expected_version}). Please refresh your view and retry."
            )

    # 2. Resource Scoping Checks
    check_institution_scope(actor, application.institution_id)
    if application.institution:
        check_regional_scope(actor, application.institution.region)

    # 3. Transition Legality & Role Authorization
    is_admin_closure = (to_stage == "CLOSED" and any(r in ADMIN_CLOSURE_ALLOWED_ROLES for r in user_roles))
    
    if not is_admin_closure:
        transitions = ALLOWED_TRANSITIONS.get(from_stage, [])
        matching_transition = None
        for target_stage, permitted_roles in transitions:
            if target_stage == to_stage:
                matching_transition = (target_stage, permitted_roles)
                break
                
        if not matching_transition:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal transition: Application cannot move from '{from_stage}' to '{to_stage}'."
            )

        _, permitted_roles = matching_transition
        if not any(r in permitted_roles for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: Role(s) '{user_roles}' not permitted to advance application from '{from_stage}' to '{to_stage}'. Required: {permitted_roles}"
            )

    # 4. Mandatory Remarks / Justification Check
    if to_stage in TRANSITIONS_REQUIRING_REASONS:
        if not remarks or not remarks.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A recorded reason/justification is mandatory for transition to '{to_stage}'."
            )

    # 5. Domain Invariant Guards
    if from_stage == "SUBMITTED" and to_stage == "AWAITING_EVC_SCHEDULE":
        is_evc_route = (application.workflow_template_code in ["ONLY_EVC", "EVC_SAC_SHC"] or application.evc_required)
        if not is_evc_route:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direct transition from 'SUBMITTED' to 'AWAITING_EVC_SCHEDULE' is only permitted for 'ONLY_EVC' or 'EVC_SAC_SHC' routes."
            )

    if to_stage == "AWAITING_EVC_SCHEDULE":
        application.evc_required = True

    if to_stage == "SCRUTINY_COMPLETED":
        # Prohibit transition if unresolved open deficiencies exist
        open_defs = db.query(Deficiency).filter(
            Deficiency.application_id == application.id,
            Deficiency.status == "OPEN"
        ).count()
        if open_defs > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot sign-off scrutiny: There are {open_defs} unresolved open deficiencies that must be cured and resolved first."
            )

    if to_stage == "RESUBMITTED":
        # Check that all open deficiencies have a cure submitted
        uncured_defs = db.query(Deficiency).filter(
            Deficiency.application_id == application.id,
            Deficiency.status == "OPEN",
            Deficiency.cure_remarks == None
        ).count()
        if uncured_defs > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resubmit: {uncured_defs} deficiency items do not have required cure explanations or documents attached."
            )

    if to_stage == "EVC_COMPLETED":
        # Check that an EVC inspection was scheduled and has a report / recommendation
        inspection = db.query(EVCInspection).filter(
            EVCInspection.application_id == application.id
        ).first()
        if not inspection or inspection.status not in ["SCHEDULED", "REPORT_SUBMITTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete EVC stage: No scheduled inspection found for this application."
            )

    if to_stage in ["AWAITING_SAC_CAC_REVIEW", "AWAITING_COMPETENT_AUTHORITY", "APPROVED"]:
        requires_evc = (
            application.workflow_template_code in ["NEW_INSTITUTION", "SCRUTINY_EVC", "EVC_SAC_SHC", "ONLY_EVC"]
            or application.evc_required
        )
        if requires_evc:
            completed_evc = db.query(EVCInspection).filter(
                EVCInspection.application_id == application.id,
                EVCInspection.status.in_(["REPORT_SUBMITTED", "RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"])
            ).first()
            if not completed_evc and from_stage not in ["EVC_COMPLETED", "AWAITING_SAC_CAC_REVIEW", "AWAITING_COMPETENT_AUTHORITY"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot advance application: Route requires mandatory EVC inspection, but no completed inspection report exists."
                )

    # 6. Apply State Mutation and Increment Version
    application.current_stage = to_stage
    application.version += 1
    now = datetime.now(timezone.utc)
    if to_stage == "APPROVED":
        application.approved_at = now
    elif to_stage == "REJECTED":
        application.rejected_at = now

    # 7. Record ApplicationStage timeline event
    actor_primary_role = user_roles[0] if user_roles else "USER"
    stage_event = ApplicationStage(
        application_id=application.id,
        from_stage=from_stage,
        to_stage=to_stage,
        actor_id=actor.id,
        actor_role=actor_primary_role,
        actor_name=actor.full_name,
        remarks=remarks,
        created_at=now
    )
    db.add(stage_event)

    # 8. Transactional Outbox & Notification Dispatch
    level = "INFO"
    if to_stage in ["DEFICIENCY_COMMUNICATED", "REJECTED"]:
        level = "DANGER"
    elif to_stage in ["APPROVED", "SCRUTINY_COMPLETED"]:
        level = "SUCCESS"

    notif_title = f"Application {application.application_number} status updated to {to_stage}"
    notif_msg = remarks or f"Application status transitioned from {from_stage} to {to_stage} by {actor.full_name}."
    link_url = f"/applications/{application.id}"

    from app.services.notification.outbox_dispatcher import OutboxDispatcherService
    inst = application.institution
    recipient_email = getattr(inst, "email", None) if inst else None

    # In-App Outbox & persistent inbox notification
    OutboxDispatcherService.queue_notification(
        db=db,
        event_type="APPLICATION_STAGE_CHANGED",
        entity_type="APPLICATION",
        entity_id=application.id,
        channel="IN_APP",
        template_code="DEFICIENCY_COMMUNICATED" if to_stage == "DEFICIENCY_COMMUNICATED" else "CURE_SUBMITTED" if to_stage == "RESUBMITTED" else "APPLICATION_STAGE_CHANGED",
        params={
            "app_num": application.application_number,
            "institution_name": inst.name if inst else f"Institution #{application.institution_id}",
            "from_stage": from_stage,
            "to_stage": to_stage,
            "remarks": remarks,
            "summary": notif_msg,
            "link_url": link_url
        },
        institution_id=application.institution_id,
        recipient_role="INSTITUTION_ADMIN",
        recipient_email=recipient_email,
        link_url=link_url,
        level=level
    )

    # External EMAIL Outbox for high-impact milestones
    if recipient_email and to_stage in ["DEFICIENCY_COMMUNICATED", "RESUBMITTED", "APPROVED", "REJECTED"]:
        email_key = f"OUTBOX:APPLICATION:{application.id}:EMAIL:{to_stage}:{len(application.stages or [])}"
        OutboxDispatcherService.queue_notification(
            db=db,
            event_type="APPLICATION_STAGE_CHANGED",
            entity_type="APPLICATION",
            entity_id=application.id,
            channel="EMAIL",
            template_code="DEFICIENCY_COMMUNICATED" if to_stage == "DEFICIENCY_COMMUNICATED" else "CURE_SUBMITTED" if to_stage == "RESUBMITTED" else "APPLICATION_STAGE_CHANGED",
            params={
                "app_num": application.application_number,
                "institution_name": inst.name if inst else f"Institution #{application.institution_id}",
                "from_stage": from_stage,
                "to_stage": to_stage,
                "remarks": remarks,
                "summary": notif_msg,
                "deadline": "15 Days" if to_stage == "DEFICIENCY_COMMUNICATED" else "Under Review",
                "link_url": link_url
            },
            institution_id=application.institution_id,
            recipient_role="INSTITUTION_ADMIN",
            recipient_email=recipient_email,
            idempotency_key=email_key,
            link_url=link_url,
            level=level
        )

    # 9. Immutable audit log (Atomic with stage transition)
    log_audit_event(
        db=db,
        action="STAGE_TRANSITION",
        entity_type="APPLICATION",
        entity_id=application.id,
        actor_id=actor.id,
        actor_name=actor.full_name,
        actor_role=actor_primary_role,
        details={
            "application_number": application.application_number,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "new_version": application.version,
            "remarks": remarks
        }
    )

    db.commit()
    db.refresh(application)
    return application

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.alert import Notification
from app.models.user import User
from app.services.audit_service import log_audit_event

ALLOWED_TRANSITIONS: Dict[str, List[Tuple[str, List[str]]]] = {
    "DRAFT": [
        ("SUBMITTED", ["INSTITUTION_ADMIN"])
    ],
    "SUBMITTED": [
        ("UNDER_SCRUTINY", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"])
    ],
    "UNDER_SCRUTINY": [
        ("DEFICIENCY_COMMUNICATED", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("SCRUTINY_COMPLETED", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("AWAITING_EVC_SCHEDULE", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("AWAITING_COMPETENT_AUTHORITY", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
    ],
    "DEFICIENCY_COMMUNICATED": [
        ("RESUBMITTED", ["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"])
    ],
    "RESUBMITTED": [
        ("UNDER_SCRUTINY", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"])
    ],
    "SCRUTINY_COMPLETED": [
        ("AWAITING_EVC_SCHEDULE", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("AWAITING_SAC_CAC_REVIEW", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("AWAITING_COMPETENT_AUTHORITY", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
    ],
    "AWAITING_EVC_SCHEDULE": [
        ("EVC_SCHEDULED", ["EVC_COORDINATOR", "REGIONAL_OFFICER", "SYSTEM_ADMIN"])
    ],
    "EVC_SCHEDULED": [
        ("EVC_COMPLETED", ["EVC_COORDINATOR", "COMMITTEE_MEMBER", "REGIONAL_OFFICER", "SYSTEM_ADMIN"])
    ],
    "EVC_COMPLETED": [
        ("AWAITING_SAC_CAC_REVIEW", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("AWAITING_COMPETENT_AUTHORITY", ["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
    ],
    "AWAITING_SAC_CAC_REVIEW": [
        ("AWAITING_COMPETENT_AUTHORITY", ["COMMITTEE_MEMBER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]),
        ("DEFICIENCY_COMMUNICATED", ["COMMITTEE_MEMBER", "BUREAU_OFFICER", "SYSTEM_ADMIN"])
    ],
    "AWAITING_COMPETENT_AUTHORITY": [
        ("APPROVED", ["COMPETENT_AUTHORITY"]),
        ("REJECTED", ["COMPETENT_AUTHORITY"]),
        ("DEFICIENCY_COMMUNICATED", ["COMPETENT_AUTHORITY"])
    ],
}

def get_allowed_transitions(current_stage: str, user_roles: List[str]) -> List[str]:
    transitions = ALLOWED_TRANSITIONS.get(current_stage, [])
    allowed = []
    for to_stage, permitted_roles in transitions:
        if any(r in permitted_roles for r in user_roles) or "SYSTEM_ADMIN" in user_roles:
            allowed.append(to_stage)
    return allowed

def execute_transition(
    db: Session,
    application: Application,
    to_stage: str,
    actor: User,
    remarks: Optional[str] = None
) -> Application:
    user_roles = [r.role for r in actor.roles]
    from_stage = application.current_stage

    # 1. Check transition legality
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
    if not any(r in permitted_roles for r in user_roles) and "SYSTEM_ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized: Role '{user_roles}' is not permitted to advance application from '{from_stage}' to '{to_stage}'. Required: {permitted_roles}"
        )

    # 2. Guard condition checks
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
        # Check that open deficiencies have cure submitted
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

    # 3. Apply state mutation
    application.current_stage = to_stage
    now = datetime.now(timezone.utc)
    if to_stage == "APPROVED":
        application.approved_at = now
    elif to_stage == "REJECTED":
        application.rejected_at = now

    # 4. Record ApplicationStage timeline event
    stage_event = ApplicationStage(
        application_id=application.id,
        from_stage=from_stage,
        to_stage=to_stage,
        actor_id=actor.id,
        actor_role=user_roles[0] if user_roles else "USER",
        actor_name=actor.full_name,
        remarks=remarks,
        created_at=now
    )
    db.add(stage_event)

    # 5. Dispatch notification
    level = "INFO"
    if to_stage in ["DEFICIENCY_COMMUNICATED", "REJECTED"]:
        level = "DANGER"
    elif to_stage in ["APPROVED", "SCRUTINY_COMPLETED"]:
        level = "SUCCESS"

    notif = Notification(
        institution_id=application.institution_id,
        title=f"Application {application.application_number} status updated to {to_stage}",
        message=remarks or f"Application status transitioned from {from_stage} to {to_stage} by {actor.full_name}.",
        level=level,
        link_url=f"/applications/{application.id}"
    )
    db.add(notif)

    # 6. Immutable audit log
    log_audit_event(
        db=db,
        action="STAGE_TRANSITION",
        entity_type="APPLICATION",
        entity_id=application.id,
        actor_id=actor.id,
        actor_name=actor.full_name,
        actor_role=user_roles[0] if user_roles else "USER",
        details={
            "application_number": application.application_number,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "remarks": remarks
        }
    )

    db.commit()
    db.refresh(application)
    return application

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.alert import Notification, AlertEscalation
from app.schemas.alert import (
    NotificationResponse, AlertEscalationResponse, AlertScanResponse,
    DeadlineEngineStatusResponse, AcknowledgeEscalationRequest
)
from app.services.deadline_service import DeadlineService
from app.services.scheduler import scheduler
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/alerts", tags=["Alerts & Deadlines"])

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    level: Optional[str] = Query(None, description="Filter by level: INFO, WARNING, DANGER, SUCCESS"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notifications scoped strictly to caller's institutional or regional authority."""
    query = db.query(Notification)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        # Strict tenant boundary: institution users see only their institution notifications
        query = query.filter(
            or_(
                Notification.institution_id == current_user.institution_id,
                Notification.user_id == current_user.id
            )
        )
    else:
        # Officer scoping: see direct messages, role broadcasts, or platform alerts
        conditions = [
            Notification.user_id == current_user.id,
            Notification.recipient_role.in_(user_roles),
            (Notification.institution_id == None) & (Notification.recipient_role == None)
        ]
        query = query.filter(or_(*conditions))

    if unread_only:
        query = query.filter(Notification.is_read == False)
    if level:
        query = query.filter(Notification.level == level)
    if entity_type:
        query = query.filter(Notification.entity_type == entity_type)

    return query.order_by(Notification.created_at.desc()).limit(100).all()

@router.post("/notifications/{id}/read")
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification read after checking ownership."""
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    # Scoping check
    if not is_officer:
        if notif.institution_id != current_user.institution_id and notif.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot mark another institution's notification as read")
    else:
        if notif.user_id and notif.user_id != current_user.id and "SYSTEM_ADMIN" not in user_roles:
            if notif.recipient_role not in user_roles:
                raise HTTPException(status_code=403, detail="Access denied: You do not have permission for this notification")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Notification marked as read", "id": notif.id}

@router.get("/escalations", response_model=List[AlertEscalationResponse])
def get_escalations(
    status_filter: Optional[str] = Query(None, description="ACTIVE, ACKNOWLEDGED, RESOLVED"),
    entity_type: Optional[str] = Query(None, description="APPLICATION, UNDERTAKING, DOCUMENT, EVC"),
    escalation_level: Optional[str] = Query(None, description="REMINDER_L1, ESCALATION_L1_RO, etc."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List escalations scoped to caller's institutional tenant or authorized regional jurisdiction."""
    query = db.query(AlertEscalation)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        # Institution users only see non-confidential alerts regarding their own institution
        query = query.filter(
            AlertEscalation.institution_id == current_user.institution_id,
            AlertEscalation.recipient_role.in_(["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"])
        )
    elif "SYSTEM_ADMIN" in user_roles or "BUREAU_OFFICER" in user_roles or "COMPETENT_AUTHORITY" in user_roles:
        # National officers can inspect all escalations
        pass
    elif "REGIONAL_OFFICER" in user_roles:
        # Regional officer strictly scoped to assigned region
        if current_user.region:
            query = query.filter(
                (AlertEscalation.region == current_user.region) | (AlertEscalation.region == None)
            )
        else:
            query = query.filter(AlertEscalation.recipient_role == "REGIONAL_OFFICER")
    else:
        # Other officer roles (e.g. EVC Coordinator)
        query = query.filter(AlertEscalation.recipient_role.in_(user_roles))

    if status_filter:
        query = query.filter(AlertEscalation.status == status_filter)
    if entity_type:
        query = query.filter(AlertEscalation.entity_type == entity_type)
    if escalation_level:
        query = query.filter(AlertEscalation.escalation_level == escalation_level)

    return query.order_by(AlertEscalation.created_at.desc()).all()

@router.post("/{id}/acknowledge")
@router.post("/escalations/{id}/acknowledge")
def acknowledge_escalation(
    id: int,
    request: Optional[AcknowledgeEscalationRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"]))
):
    """Acknowledge an escalation within authorized jurisdiction."""
    esc = db.query(AlertEscalation).filter(AlertEscalation.id == id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation record not found")

    user_roles = [r.role for r in current_user.roles]
    # Regional Officer jurisdiction check
    if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if esc.region and current_user.region and esc.region != current_user.region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Regional Officer for {current_user.region} cannot acknowledge escalations in {esc.region} region."
            )

    esc.status = "ACKNOWLEDGED"
    esc.acknowledged_by_id = current_user.id
    esc.acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    actor_role = current_user.roles[0].role if current_user.roles else "OFFICER"
    log_audit_event(
        db=db,
        action="ESCALATION_ACKNOWLEDGED",
        entity_type="ALERT_ESCALATION",
        entity_id=esc.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={
            "escalation_level": esc.escalation_level,
            "entity_type": esc.entity_type,
            "entity_id": esc.entity_id,
            "remarks": request.remarks if request else None
        }
    )

    return {"message": "Escalation acknowledged", "status": "ACKNOWLEDGED", "id": esc.id}

@router.get("/engine-status", response_model=DeadlineEngineStatusResponse)
def get_deadline_engine_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Inspect background deadline scheduler status, last execution, and lifetime metrics."""
    return scheduler.get_status(db)

@router.post("/run-scan", response_model=AlertScanResponse)
def trigger_deadline_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER"]))
):
    """Triggers an on-demand deadline scan using the canonical deadline engine."""
    result = DeadlineService.run_deadline_and_escalation_scan(db, trigger_mode="MANUAL")

    actor_role = current_user.roles[0].role if current_user.roles else "SYSTEM_ADMIN"
    log_audit_event(
        db=db,
        action="DEADLINE_SCAN_EXECUTED",
        entity_type="SYSTEM",
        entity_id=0,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details=result
    )

    return AlertScanResponse(**result)

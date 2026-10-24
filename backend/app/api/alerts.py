from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.alert import Notification, AlertEscalation
from app.schemas.alert import NotificationResponse, AlertEscalationResponse, AlertScanResponse
from app.services.deadline_service import run_deadline_and_escalation_scan
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/alerts", tags=["Alerts & Deadlines"])

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Notification)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        query = query.filter(Notification.institution_id == current_user.institution_id)
    else:
        # Officers see platform and regional notifications
        query = query.filter((Notification.user_id == current_user.id) | (Notification.institution_id == None))

    return query.order_by(Notification.created_at.desc()).limit(50).all()

@router.get("/escalations", response_model=List[AlertEscalationResponse])
def get_escalations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AlertEscalation)
    user_roles = [r.role for r in current_user.roles]
    if "SYSTEM_ADMIN" not in user_roles and "COMPETENT_AUTHORITY" not in user_roles:
        query = query.filter(AlertEscalation.recipient_role.in_(user_roles))
    return query.order_by(AlertEscalation.created_at.desc()).all()

@router.post("/run-scan", response_model=AlertScanResponse)
def trigger_deadline_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers the idempotent deadline evaluation scanner"""
    result = run_deadline_and_escalation_scan(db)
    
    log_audit_event(
        db=db,
        action="DEADLINE_SCAN_EXECUTED",
        entity_type="SYSTEM",
        entity_id=0,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.roles[0].role if current_user.roles else "OFFICER",
        details=result
    )
    db.commit()

    return AlertScanResponse(**result)

@router.post("/{id}/acknowledge")
def acknowledge_escalation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    esc = db.query(AlertEscalation).filter(AlertEscalation.id == id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation record not found")

    esc.status = "ACKNOWLEDGED"
    esc.acknowledged_by_id = current_user.id
    esc.acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Escalation acknowledged", "status": "ACKNOWLEDGED"}

@router.post("/notifications/{id}/read")
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "Notification marked as read"}

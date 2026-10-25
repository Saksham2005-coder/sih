import csv
import io
from datetime import datetime, timezone
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.audit import AuditEvent
from app.schemas.audit import AuditExplorerResponse, AuditEventResponse
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/audit", tags=["Audit Explorer"])

def sanitize_csv_cell(val: Any) -> str:
    """Mitigates CSV Formula Injection (DDE) risks by prepending single quote to formula triggers."""
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

def apply_audit_scoping(query, current_user: User):
    """Enforces strict tenant isolation and regional jurisdiction on audit event queries."""
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer and current_user.institution_id:
        query = query.filter(AuditEvent.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(
            or_(
                AuditEvent.region == current_user.region,
                AuditEvent.region == None
            )
        )
    return query


@router.get("", response_model=AuditExplorerResponse)
def get_audit_trail(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    actor_role: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "REGIONAL_OFFICER", "BUREAU_OFFICER",
        "COMMITTEE_MEMBER", "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Query append-only audit trail with multi-field filtering, regional scoping, and pagination."""
    query = db.query(AuditEvent)
    query = apply_audit_scoping(query, current_user)

    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if action:
        query = query.filter(AuditEvent.action == action)
    if actor_role:
        query = query.filter(AuditEvent.actor_role == actor_role)
    if date_from:
        query = query.filter(AuditEvent.created_at >= date_from)
    if date_to:
        query = query.filter(AuditEvent.created_at <= date_to)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                AuditEvent.actor_name.ilike(s),
                AuditEvent.action.ilike(s),
                AuditEvent.details.ilike(s)
            )
        )

    total = query.count()
    items = query.order_by(AuditEvent.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return AuditExplorerResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/export")
def export_audit_csv(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Exports sanitized, formula-injection safe CSV of audit events with export audit logging."""
    query = db.query(AuditEvent)
    query = apply_audit_scoping(query, current_user)

    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if action:
        query = query.filter(AuditEvent.action == action)

    events = query.order_by(AuditEvent.created_at.desc()).limit(1000).all()

    # Log an audit record for this export event
    log_audit_event(
        db=db,
        action="AUDIT_EXPORTED",
        entity_type="AUDIT",
        entity_id=0,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.roles[0].role if current_user.roles else "OFFICER",
        details={"record_count": len(events), "entity_type_filter": entity_type, "action_filter": action}
    )
    db.commit()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event ID", "Timestamp (UTC)", "Actor Name", "Actor Role",
        "Action", "Entity Type", "Entity ID", "Details", "IP Address"
    ])

    for ev in events:
        writer.writerow([
            sanitize_csv_cell(ev.id),
            sanitize_csv_cell(ev.created_at.isoformat() if ev.created_at else ""),
            sanitize_csv_cell(ev.actor_name),
            sanitize_csv_cell(ev.actor_role),
            sanitize_csv_cell(ev.action),
            sanitize_csv_cell(ev.entity_type),
            sanitize_csv_cell(ev.entity_id),
            sanitize_csv_cell(ev.details),
            sanitize_csv_cell(ev.ip_address)
        ])

    output.seek(0)
    filename = f"reguflow_audit_log_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

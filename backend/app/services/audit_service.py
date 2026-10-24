import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = "127.0.0.1"
) -> AuditEvent:
    details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
    event = AuditEvent(
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_str,
        ip_address=ip_address
    )
    db.add(event)
    return event

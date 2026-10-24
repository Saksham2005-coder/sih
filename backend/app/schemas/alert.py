from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    institution_id: Optional[int] = None
    title: str
    message: str
    channel: str
    level: str
    is_read: bool
    link_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertEscalationResponse(BaseModel):
    id: int
    idempotency_key: str
    entity_type: str
    entity_id: int
    trigger_type: str
    threshold_days: int
    escalation_level: str
    recipient_role: str
    recipient_user_id: Optional[int] = None
    status: str
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertScanResponse(BaseModel):
    scanned_entities: int
    reminders_created: int
    escalations_created: int
    duplicates_prevented: int
    execution_time_ms: float

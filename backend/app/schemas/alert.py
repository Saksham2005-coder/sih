from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    institution_id: Optional[int] = None
    recipient_role: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    title: str
    message: str
    channel: str
    delivery_channel: str
    delivery_status: str
    level: str
    is_read: bool
    read_at: Optional[datetime] = None
    link_url: Optional[str] = None
    created_at: datetime

class AlertEscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    idempotency_key: str
    entity_type: str
    entity_id: int
    trigger_type: str
    threshold_days: int
    escalation_level: str
    recipient_role: str
    recipient_user_id: Optional[int] = None
    region: Optional[str] = None
    institution_id: Optional[int] = None
    cycle_id: Optional[str] = None
    rule_code: Optional[str] = None
    rule_version: Optional[str] = None
    status: str
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_reason: Optional[str] = None
    created_at: datetime

class AlertScanResponse(BaseModel):
    scanned_entities: int
    reminders_created: int
    escalations_created: int
    duplicates_prevented: int
    resolved_count: int
    execution_time_ms: float
    trigger_mode: Optional[str] = "MANUAL"

class DeadlineEngineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: str
    trigger_mode: str
    scanned_entities: int
    reminders_created: int
    escalations_created: int
    duplicates_prevented: int
    resolved_count: int
    execution_time_ms: float
    status: str
    error_message: Optional[str] = None
    created_at: datetime

class DeadlineEngineStatusResponse(BaseModel):
    is_running: bool
    scan_interval_seconds: int
    last_run: Optional[DeadlineEngineRunResponse] = None
    total_runs: int
    total_scanned: int
    total_reminders: int
    total_escalations: int
    total_duplicates_prevented: int

class AcknowledgeEscalationRequest(BaseModel):
    remarks: Optional[str] = None


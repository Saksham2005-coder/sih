from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationOutboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idempotency_key: str
    correlation_id: str
    event_type: str
    entity_type: str
    entity_id: int
    institution_id: Optional[int] = None
    region: Optional[str] = None
    recipient_role: Optional[str] = None
    recipient_user_id: Optional[int] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    channel: str
    template_code: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    link_url: Optional[str] = None
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    last_error_category: Optional[str] = None
    last_error_message: Optional[str] = None
    provider_message_id: Optional[str] = None
    provider_response: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class NotificationOutboxSummaryResponse(BaseModel):
    total: int
    queued: int
    processing: int
    accepted_by_provider: int
    simulated: int
    not_configured: int
    retry_scheduled: int
    dead_letter: int
    failed: int


class ChannelHealthStatus(BaseModel):
    channel: str
    transport: str
    is_configured: bool
    status: str
    details: Dict[str, Any]


class NotificationChannelStatusResponse(BaseModel):
    channels: List[ChannelHealthStatus]
    active_sse_subscribers: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
    total_count: int

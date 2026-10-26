from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
from app.core.database import Base


class NotificationOutbox(Base):
    """
    Transactional Notification Outbox.
    Records every notification dispatch intent atomically within the originating business transaction.
    Guarantees reliable external channel delivery (Email, SMS) and persistent auditing.
    """
    __tablename__ = "notification_outbox"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(160), unique=True, index=True, nullable=False)
    correlation_id = Column(String(64), index=True, nullable=False)

    # Business entity provenance
    event_type = Column(String(64), index=True, nullable=False)  # e.g. APPLICATION_STAGE_CHANGED, SLA_WARNING
    entity_type = Column(String(64), index=True, nullable=False)  # APPLICATION, UNDERTAKING, DOCUMENT, etc.
    entity_id = Column(Integer, index=True, nullable=False)

    # Scoping & Jurisdiction
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    region = Column(String(64), nullable=True, index=True)
    recipient_role = Column(String(64), nullable=True, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Addressing
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(32), nullable=True)
    channel = Column(String(32), index=True, nullable=False)  # EMAIL, SMS, IN_APP

    # Message Content
    template_code = Column(String(64), nullable=False)
    subject = Column(String(255), nullable=False)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    link_url = Column(String(255), nullable=True)
    payload_json = Column(JSON, nullable=True)

    # Delivery State Machine:
    # QUEUED -> PROCESSING -> ACCEPTED_BY_PROVIDER | SIMULATED | NOT_CONFIGURED | RETRY_SCHEDULED | DEAD_LETTER
    status = Column(String(32), default="QUEUED", index=True, nullable=False)

    # Retry Tracking & Exponential Backoff
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=4, nullable=False)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    last_attempt_at = Column(DateTime, nullable=True)

    # Outcome & Diagnostics
    last_error_category = Column(String(64), nullable=True)  # TIMEOUT, NETWORK_ERROR, CONFIGURATION_MISSING, etc.
    last_error_message = Column(Text, nullable=True)
    provider_message_id = Column(String(128), nullable=True)
    provider_response = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

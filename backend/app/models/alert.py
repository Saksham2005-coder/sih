from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from datetime import datetime, timezone
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    recipient_role = Column(String(64), nullable=True, index=True)
    entity_type = Column(String(64), nullable=True) # APPLICATION, UNDERTAKING, DOCUMENT, EVC
    entity_id = Column(Integer, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(32), default="IN_APP", nullable=False)
    delivery_channel = Column(String(32), default="IN_APP", nullable=False) # IN_APP, EMAIL, SMS
    delivery_status = Column(String(32), default="DELIVERED", nullable=False) # DELIVERED, QUEUED, SIMULATED, FAILED
    level = Column(String(32), default="INFO", nullable=False) # INFO, WARNING, DANGER, SUCCESS
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AlertEscalation(Base):
    __tablename__ = "alert_escalations"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    entity_type = Column(String(64), nullable=False) # APPLICATION, UNDERTAKING, DOCUMENT, EVC
    entity_id = Column(Integer, nullable=False, index=True)
    trigger_type = Column(String(64), nullable=False) # SLA_APPROACHING, SLA_OVERDUE, EXPIRY_WARNING, DEFICIENCY_OVERDUE, EVC_SCHEDULE_OVERDUE, VERIFICATION_OVERDUE
    threshold_days = Column(Integer, nullable=False)
    escalation_level = Column(String(64), nullable=False) # REMINDER_L1, REMINDER_L2, ESCALATION_L1_RO, ESCALATION_L2_BO, ESCALATION_L3_MEMBER_SEC
    recipient_role = Column(String(64), nullable=False)
    recipient_user_id = Column(Integer, nullable=True)
    region = Column(String(64), nullable=True, index=True)
    institution_id = Column(Integer, nullable=True, index=True)
    cycle_id = Column(String(64), default="1", nullable=True)
    rule_code = Column(String(64), nullable=True)
    rule_version = Column(String(16), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, ACKNOWLEDGED, RESOLVED
    acknowledged_by_id = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class DeadlineEngineRun(Base):
    __tablename__ = "deadline_engine_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    trigger_mode = Column(String(32), default="SCHEDULED", nullable=False) # SCHEDULED, MANUAL
    scanned_entities = Column(Integer, default=0, nullable=False)
    reminders_created = Column(Integer, default=0, nullable=False)
    escalations_created = Column(Integer, default=0, nullable=False)
    duplicates_prevented = Column(Integer, default=0, nullable=False)
    resolved_count = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False) # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class SchedulerLease(Base):
    __tablename__ = "scheduler_leases"

    id = Column(Integer, primary_key=True, index=True)
    lease_name = Column(String(64), unique=True, index=True, nullable=False) # e.g. "deadline_engine_scan"
    holder_id = Column(String(128), nullable=False) # worker instance identifier
    acquired_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


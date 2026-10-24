from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(32), default="IN_APP", nullable=False)
    level = Column(String(32), default="INFO", nullable=False) # INFO, WARNING, DANGER, SUCCESS
    is_read = Column(Boolean, default=False, nullable=False)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class AlertEscalation(Base):
    __tablename__ = "alert_escalations"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    entity_type = Column(String(64), nullable=False) # APPLICATION, UNDERTAKING, DOCUMENT, EVC
    entity_id = Column(Integer, nullable=False, index=True)
    trigger_type = Column(String(64), nullable=False) # SLA_APPROACHING, SLA_OVERDUE, EXPIRY_WARNING
    threshold_days = Column(Integer, nullable=False)
    escalation_level = Column(String(64), nullable=False) # REMINDER_L1, ESCALATION_L1_RO, ESCALATION_L2_BO, ESCALATION_L3_MEMBER_SEC
    recipient_role = Column(String(64), nullable=False)
    recipient_user_id = Column(Integer, nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, ACKNOWLEDGED, RESOLVED
    acknowledged_by_id = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

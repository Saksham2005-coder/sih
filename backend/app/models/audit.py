from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True, index=True)
    actor_name = Column(String(128), nullable=True)
    actor_role = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False, index=True) # STAGE_TRANSITION, DEFICIENCY_ISSUED, DEFICIENCY_CURED, EVIDENCE_SUBMITTED, EVIDENCE_VERIFIED, EVC_SCHEDULED, RULE_UPDATED
    entity_type = Column(String(64), nullable=False, index=True) # APPLICATION, DEFICIENCY, UNDERTAKING, DOCUMENT, EVC, RULE
    entity_id = Column(Integer, nullable=False, index=True)
    details = Column(Text, nullable=True) # JSON or formatted details
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

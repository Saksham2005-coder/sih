from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class RuleDefinition(Base):
    __tablename__ = "rule_definitions"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(64), unique=True, index=True, nullable=False) # e.g. "RULE_EOA_SLA", "RULE_DEFICIENCY_CURE", "RULE_EVC_SCHEDULE"
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False) # WORKFLOW, DEADLINE, ESCALATION, COMPLIANCE
    version = Column(String(16), default="1.0.0", nullable=False)
    config_json = Column(Text, nullable=False) # Configurable parameters (thresholds, stages, roles)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

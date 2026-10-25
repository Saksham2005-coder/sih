from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class RuleDefinition(Base):
    __tablename__ = "rule_definitions"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(64), unique=True, index=True, nullable=False) # e.g. "RULE_EOA_SLA", "RULE_DEFICIENCY_CURE", "RULE_EVC_SCHEDULE"
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False) # WORKFLOW, DEADLINE, ESCALATION, COMPLIANCE, PRIORITY
    version = Column(String(16), default="1.0.0", nullable=False)
    config_json = Column(Text, nullable=False) # Configurable parameters (thresholds, stages, roles)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="PUBLISHED", nullable=False) # DRAFT, VALIDATED, PUBLISHED, RETIRED
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_reason = Column(Text, nullable=True)
    effective_from = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    history = relationship("RuleVersionHistory", back_populates="rule", cascade="all, delete-orphan", order_by="RuleVersionHistory.created_at.desc()")

class RuleVersionHistory(Base):
    __tablename__ = "rule_version_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rule_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(64), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    category = Column(String(64), nullable=False)
    config_json = Column(Text, nullable=False)
    status = Column(String(32), default="PUBLISHED", nullable=False)
    change_reason = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    rule = relationship("RuleDefinition", back_populates="history")

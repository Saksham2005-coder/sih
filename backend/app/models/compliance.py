from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class ComplianceUndertaking(Base):
    __tablename__ = "compliance_undertakings"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False) # INFRASTRUCTURE, SAFETY, FACULTY, ACADEMIC, ACCESSIBILITY
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(32), default="NOT_YET_DUE", nullable=False, index=True) # NOT_YET_DUE, DUE_SOON, PENDING_VERIFICATION, UNDER_VERIFICATION, CORRECTION_REQUIRED, VERIFIED, DEFICIENT, OVERDUE
    
    rule_code = Column(String(64), nullable=True)
    responsible_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    evidence_type = Column(String(64), nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)

    verified_at = Column(DateTime, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    institution = relationship("Institution", back_populates="undertakings")
    application = relationship("Application", back_populates="undertakings")
    evidences = relationship("ComplianceEvidence", back_populates="undertaking", cascade="all, delete-orphan", order_by="ComplianceEvidence.version.desc()")

class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidence"

    id = Column(Integer, primary_key=True, index=True)
    undertaking_id = Column(Integer, ForeignKey("compliance_undertakings.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    remarks = Column(Text, nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    verification_status = Column(String(32), default="PENDING", nullable=False) # PENDING, VERIFIED, CORRECTION_REQUIRED, REJECTED
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    undertaking = relationship("ComplianceUndertaking", back_populates="evidences")

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(64), unique=True, index=True, nullable=False) # e.g. "AICTE-2026-EOA-98124"
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(16), nullable=False, default="2026-2027")
    application_type = Column(String(64), nullable=False, default="EOA_ANNUAL") # EOA_ANNUAL, NEW_INSTITUTION, INTAKE_VARIATION, CLOSURE_PROGRAM
    workflow_template_code = Column(String(64), nullable=False, default="EOA_ANNUAL")
    current_stage = Column(String(64), nullable=False, default="SUBMITTED", index=True)
    scrutiny_officer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    priority_score = Column(Integer, default=0, nullable=False) # 0-100
    priority_factors = Column(Text, nullable=True) # JSON string explaining score
    version = Column(Integer, default=1, nullable=False)
    evc_required = Column(Boolean, default=False, nullable=False)
    
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution = relationship("Institution", back_populates="applications")
    stages = relationship("ApplicationStage", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStage.created_at.asc()")
    deficiencies = relationship("Deficiency", back_populates="application", cascade="all, delete-orphan", order_by="Deficiency.created_at.desc()")
    evc_inspections = relationship("EVCInspection", back_populates="application", cascade="all, delete-orphan")
    undertakings = relationship("ComplianceUndertaking", back_populates="application")
    documents = relationship("DocumentRecord", back_populates="application")

class ApplicationStage(Base):
    __tablename__ = "application_stages"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stage = Column(String(64), nullable=True)
    to_stage = Column(String(64), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(String(64), nullable=True)
    actor_name = Column(String(128), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", back_populates="stages")

class Deficiency(Base):
    __tablename__ = "deficiencies"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(64), nullable=False) # INFRASTRUCTURE, FACULTY_CADRE, LAND_TITLE, FINANCIAL_AUDIT, SAFETY
    description = Column(Text, nullable=False)
    required_document = Column(String(255), nullable=True)
    status = Column(String(32), default="OPEN", nullable=False) # OPEN, CURED, WAIVED
    
    # Institution cure payload
    cure_document_url = Column(String(512), nullable=True)
    cure_remarks = Column(Text, nullable=True)
    cured_at = Column(DateTime, nullable=True)
    
    # Officer resolution
    resolved_by_officer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", back_populates="deficiencies")

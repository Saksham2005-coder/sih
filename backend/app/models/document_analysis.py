from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_record_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=True, index=True)
    document_version_id = Column(Integer, ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    compliance_evidence_id = Column(Integer, ForeignKey("compliance_evidence.id", ondelete="CASCADE"), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Lifecycle Status: QUEUED, PROCESSING, REVIEW_REQUIRED, CONFIRMED, FAILED
    status = Column(String(32), default="QUEUED", nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)

    # Extraction Engine Telemetry
    extraction_engine = Column(String(64), nullable=False, default="pypdf-text-v1")
    engine_version = Column(String(32), nullable=False, default="1.0.0")
    ocr_applied = Column(Boolean, default=False, nullable=False)
    ocr_provider = Column(String(64), default="UNAVAILABLE", nullable=False) # NONE, UNAVAILABLE, TESSERACT

    # Document Physical Attributes
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    has_text_layer = Column(Boolean, default=True, nullable=False)
    is_scanned = Column(Boolean, default=False, nullable=False)

    # Extracted Candidate Fields (dict of field_name -> CandidateFieldDict)
    # e.g. {"expiry_date": {"value": "2029-03-31", "confidence": 0.95, "source_page": 1, "source_excerpt": "..."}}
    extracted_fields = Column(JSON, default=dict, nullable=False)

    # Cross-Check Validation Findings (list of FindingDict)
    # e.g. [{"field": "expiry_date", "status": "MATCH", "severity": "INFO", "description": "..."}]
    cross_check_findings = Column(JSON, default=list, nullable=False)

    overall_confidence = Column(Float, default=0.0, nullable=False)
    summary_findings = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Human Review Decision & Audit Trail
    reviewer_decision = Column(String(32), nullable=True) # CONFIRMED, CORRECTED, REJECTED
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_remarks = Column(Text, nullable=True)
    corrected_fields = Column(JSON, nullable=True)

    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document_record = relationship("DocumentRecord", foreign_keys=[document_record_id])
    document_version = relationship("DocumentVersion", foreign_keys=[document_version_id])
    compliance_evidence = relationship("ComplianceEvidence", foreign_keys=[compliance_evidence_id])
    institution = relationship("Institution", foreign_keys=[institution_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])

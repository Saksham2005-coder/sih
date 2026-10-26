from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExtractedFieldCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    value: Optional[str] = None
    confidence: float = 0.0
    source_page: Optional[int] = None
    source_excerpt: Optional[str] = None
    field_label: Optional[str] = None

class CrossCheckFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field: str
    rule_code: str
    status: str # MATCH, POSSIBLE_MISMATCH, MISSING_EVIDENCE, EXTRACTION_UNAVAILABLE, HUMAN_REVIEW_REQUIRED
    severity: str # INFO, WARNING, CRITICAL
    entered_value: Optional[str] = None
    extracted_value: Optional[str] = None
    source_page: Optional[int] = None
    source_excerpt: Optional[str] = None
    description: str

class DocumentAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_record_id: Optional[int] = None
    document_version_id: Optional[int] = None
    compliance_evidence_id: Optional[int] = None
    institution_id: int
    institution_name: Optional[str] = None
    status: str # QUEUED, PROCESSING, REVIEW_REQUIRED, CONFIRMED, FAILED
    idempotency_key: str
    extraction_engine: str
    engine_version: str
    ocr_applied: bool
    ocr_provider: str
    file_name: str
    file_size: Optional[int] = None
    checksum_sha256: str
    page_count: int
    has_text_layer: bool
    is_scanned: bool
    extracted_fields: Dict[str, Any]
    cross_check_findings: List[CrossCheckFinding]
    overall_confidence: float
    summary_findings: Optional[str] = None
    error_message: Optional[str] = None
    reviewer_decision: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_remarks: Optional[str] = None
    corrected_fields: Optional[Dict[str, Any]] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class DocumentAnalysisReviewRequest(BaseModel):
    decision: str = Field(..., pattern="^(CONFIRMED|CORRECTED|REJECTED)$")
    reviewer_remarks: str = Field(..., min_length=5, description="Mandatory remarks by reviewing officer")
    corrected_fields: Optional[Dict[str, Any]] = None
    apply_to_record: bool = False

class DocumentAnalysisTriggerRequest(BaseModel):
    document_record_id: Optional[int] = None
    document_version_id: Optional[int] = None
    compliance_evidence_id: Optional[int] = None
    force_retry: bool = False

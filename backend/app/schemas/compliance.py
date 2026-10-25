from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ComplianceEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    undertaking_id: int
    version: int
    file_name: str
    file_url: str
    checksum_sha256: str
    remarks: Optional[str] = None
    submitted_by_id: Optional[int] = None
    submitted_at: datetime
    verification_status: str = "PENDING"
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None

class ComplianceUndertakingCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    due_date: datetime
    application_id: Optional[int] = None
    rule_code: Optional[str] = None
    evidence_type: Optional[str] = "PDF_DOCUMENT"

class ComplianceUndertakingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    application_id: Optional[int] = None
    title: str
    category: str
    description: Optional[str] = None
    due_date: datetime
    status: str
    effective_status: Optional[str] = None
    rule_code: Optional[str] = None
    responsible_user_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    evidence_type: Optional[str] = None
    fulfilled_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    created_at: datetime
    evidences: List[ComplianceEvidenceResponse] = []

class ComplianceVerifyRequest(BaseModel):
    status: str # VERIFIED, CORRECTION_REQUIRED, DEFICIENT
    notes: Optional[str] = None

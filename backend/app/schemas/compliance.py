from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ComplianceEvidenceResponse(BaseModel):
    id: int
    undertaking_id: int
    version: int
    file_name: str
    file_url: str
    checksum_sha256: str
    remarks: Optional[str] = None
    submitted_by_id: Optional[int] = None
    submitted_at: datetime

    class Config:
        from_attributes = True

class ComplianceUndertakingCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    due_date: datetime

class ComplianceUndertakingResponse(BaseModel):
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    title: str
    category: str
    description: Optional[str] = None
    due_date: datetime
    status: str
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    created_at: datetime
    evidences: List[ComplianceEvidenceResponse] = []

    class Config:
        from_attributes = True

class ComplianceVerifyRequest(BaseModel):
    status: str # VERIFIED or DEFICIENT
    notes: Optional[str] = None

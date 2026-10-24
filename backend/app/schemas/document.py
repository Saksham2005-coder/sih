from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class DocumentVersionResponse(BaseModel):
    id: int
    document_record_id: int
    version: int
    file_name: str
    file_url: str
    checksum_sha256: str
    uploaded_by_id: Optional[int] = None
    uploaded_at: datetime
    verification_status: str
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentRecordResponse(BaseModel):
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    document_type: str
    title: str
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: str
    current_version: int
    created_at: datetime
    versions: List[DocumentVersionResponse] = []

    class Config:
        from_attributes = True

class DocumentVerifyRequest(BaseModel):
    verification_status: str # VERIFIED or REJECTED
    verification_notes: Optional[str] = None

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime

class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_record_id: int
    version: int
    file_name: str
    file_url: str
    storage_key: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum_sha256: str
    renewal_reason: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    uploaded_at: datetime
    verification_status: str
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None

class DocumentRecordCreate(BaseModel):
    document_type: str
    title: str
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    valid_from: Optional[date] = None
    expiry_date: Optional[date] = None
    renewal_required: bool = True
    application_id: Optional[int] = None

class DocumentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    application_id: Optional[int] = None
    document_type: str
    title: str
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    valid_from: Optional[date] = None
    expiry_date: Optional[date] = None
    renewal_required: bool = True
    status: str
    current_version: int
    created_at: datetime
    versions: List[DocumentVersionResponse] = []

class DocumentVerifyRequest(BaseModel):
    verification_status: str # VERIFIED or REJECTED
    verification_notes: str # Mandatory notes

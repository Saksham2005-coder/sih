from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class StatutoryOrderGenerateRequest(BaseModel):
    application_id: int
    remarks: Optional[str] = None
    custom_remarks: Optional[str] = None
    additional_conditions: Optional[List[str]] = None
    override_reason: Optional[str] = None
    template_version: Optional[str] = "1.0.0"

class StatutoryOrderRevokeRequest(BaseModel):
    revocation_reason: str = Field(..., min_length=10, description="Mandatory statutory justification for revoking an issued order.")

class StatutoryOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    application_number: str
    institution_id: int
    institution_name: str
    order_number: str
    decision: str # APPROVED, REJECTED
    status: str # ACTIVE, SUPERSEDED, REVOKED
    version: int
    order_date: date
    decision_recorded_at: datetime
    issued_by_id: Optional[int] = None
    issued_by_name: str
    issued_by_designation: str
    decision_remarks: str
    conditions: List[Dict[str, Any]]
    reference_identifiers: Dict[str, Any]
    pdf_filename: str
    pdf_storage_key: str
    pdf_url: str
    checksum_sha256: str
    verification_token: str
    verification_url: str
    template_version: str
    signature_status: str
    signing_provider: str
    signing_metadata: Dict[str, Any]
    signature_disclaimer: str
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    superseded_by_order_id: Optional[int] = None
    superseded_at: Optional[datetime] = None
    superseding_reason: Optional[str] = None
    created_at: datetime

class StatutoryOrderPublicVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_authentic: bool
    verification_status: str # VERIFIED_AUTHENTIC, TAMPERED_HASH_MISMATCH, REVOKED, NOT_FOUND
    artifact_hash_match: bool
    order_number: str
    application_number: str
    institution_name: str
    regional_office: str
    decision: str
    order_date: date
    version: int
    status: str # ACTIVE, SUPERSEDED, REVOKED
    order_status: Optional[str] = None
    is_revoked: bool
    revocation_reason: Optional[str] = None
    superseded_by: Optional[str] = None
    checksum_sha256: str
    signature_status: str # UNSIGNED_PROTOTYPE
    signing_provider: str
    signature_disclaimer: str
    regulatory_disclaimer: Optional[str] = None
    status_details: str
    verified_at: datetime

class OrderArtifactVerifyUploadResponse(BaseModel):
    is_valid: bool
    is_match: bool
    verification_status: str # AUTHENTIC_MATCH, NO_MATCH_FOUND, TAMPERED_OR_UNREGISTERED
    integrity_status: Optional[str] = None
    order_number: Optional[str] = None
    matched_order_number: Optional[str] = None
    decision: Optional[str] = None
    version: Optional[int] = None
    institution_name: Optional[str] = None
    computed_checksum_sha256: str
    stored_checksum_sha256: Optional[str] = None
    message: str

from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class DeficiencyCreateRequest(BaseModel):
    category: str
    description: str
    required_document: Optional[str] = None

class DeficiencyCureRequest(BaseModel):
    cure_remarks: str
    cure_document_url: Optional[str] = None

class DeficiencyResponse(BaseModel):
    id: int
    application_id: int
    category: str
    description: str
    required_document: Optional[str] = None
    status: str
    cure_document_url: Optional[str] = None
    cure_remarks: Optional[str] = None
    cured_at: Optional[datetime] = None
    resolved_by_officer_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationStageResponse(BaseModel):
    id: int
    application_id: int
    from_stage: Optional[str] = None
    to_stage: str
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    actor_name: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationCreateRequest(BaseModel):
    application_type: str = "EOA_ANNUAL"
    academic_year: str = "2026-2027"

class ApplicationTransitionRequest(BaseModel):
    to_stage: str
    remarks: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    application_number: str
    institution_id: int
    institution_name: Optional[str] = None
    region: Optional[str] = None
    academic_year: str
    application_type: str
    workflow_template_code: str
    current_stage: str
    scrutiny_officer_id: Optional[int] = None
    priority_score: int
    priority_factors: Optional[Any] = None
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    open_deficiencies_count: int = 0

    class Config:
        from_attributes = True

class ApplicationDetailResponse(ApplicationResponse):
    stages: List[ApplicationStageResponse] = []
    deficiencies: List[DeficiencyResponse] = []

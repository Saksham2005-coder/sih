from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class EVCScheduleRequest(BaseModel):
    application_id: int
    inspection_type: str = "PHYSICAL_ONSITE"
    scheduled_date: datetime
    convener_name: str
    expert_member_name: str

class EVCReportSubmitRequest(BaseModel):
    report_url: str
    report_notes: str
    recommendation: str # RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION, DEFICIENCY_NOTED

class EVCInspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    application_number: Optional[str] = None
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    region: Optional[str] = None
    inspection_type: str
    scheduled_date: Optional[datetime] = None
    convener_name: Optional[str] = None
    expert_member_name: Optional[str] = None
    status: str
    report_url: Optional[str] = None
    report_notes: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
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
    recommendation: str  # RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION, DEFICIENCY_NOTED
    virtual_meeting_url: Optional[str] = None
    virtual_recording_url: Optional[str] = None


class EVCExpertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    designation: str
    expertise_categories: List[str]
    specializations: List[str]
    current_institution: str
    institution_id: Optional[int] = None
    parent_organization: Optional[str] = None
    district: Optional[str] = None
    region: str
    is_active: bool
    availability_status: str
    declared_conflicts: List[Dict[str, Any]]
    prior_inspections: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class COICheckRequest(BaseModel):
    expert_id: int
    application_id: int
    cooling_off_years: Optional[int] = 3


class COIRuleResult(BaseModel):
    rule_code: str
    rule_name: str
    status: str  # PASSED, FAILED
    details: str


class COICheckResponse(BaseModel):
    expert_id: int
    expert_name: str
    current_institution: str
    is_prohibited: bool
    can_override: bool
    summary: str
    rules_checked: List[COIRuleResult]
    assessed_at: str
    data_completeness: Optional[str] = "COMPLETE"


class EVCPanelProposeRequest(BaseModel):
    inspection_id: int
    expert_id: int
    panel_role: str = "EXPERT_MEMBER"  # CONVENER, EXPERT_MEMBER
    override_reason: Optional[str] = None


class EVCPanelAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    expert_id: int
    expert_name: Optional[str] = None
    expert_email: Optional[str] = None
    expert_institution: Optional[str] = None
    panel_role: str
    status: str
    invited_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    coi_check_result: Optional[Dict[str, Any]] = None
    override_applied: bool
    override_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EVCInvitationDeclineRequest(BaseModel):
    reason: str


class EVCReassignRequest(BaseModel):
    new_expert_id: int
    override_reason: Optional[str] = None


class EVCCheckInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    source: Optional[str] = "BROWSER_GEOLOCATION"


class EVCFieldEvidenceCreateRequest(BaseModel):
    checklist_item_code: str
    requirement_title: str
    observation_notes: str
    status: str = "COMPLIANT"  # COMPLIANT, DEFICIENT, NOT_APPLICABLE, PENDING_REVIEW
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    evidence_type: str = "PHOTO"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    source: Optional[str] = "BROWSER_GEOLOCATION"
    permission_granted: bool = False


class EVCFieldEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    checklist_item_code: str
    requirement_title: str
    observation_notes: str
    status: str
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    evidence_type: str
    captured_by_id: Optional[int] = None
    captured_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy_meters: Optional[float] = None
    location_capture_source: Optional[str] = None
    location_permission_granted: bool
    created_at: datetime
    updated_at: datetime


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
    coordinator_id: Optional[int] = None
    status: str
    panel_status: Optional[str] = "PENDING_PANEL"
    check_in_at: Optional[datetime] = None
    check_in_lat: Optional[float] = None
    check_in_lon: Optional[float] = None
    check_in_accuracy: Optional[float] = None
    check_in_source: Optional[str] = None
    virtual_meeting_url: Optional[str] = None
    virtual_recording_url: Optional[str] = None
    report_url: Optional[str] = None
    report_notes: Optional[str] = None
    recommendation: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    panel_assignments: Optional[List[EVCPanelAssignmentResponse]] = None
    field_evidence: Optional[List[EVCFieldEvidenceResponse]] = None

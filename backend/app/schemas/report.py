from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime

class OperationalSummaryResponse(BaseModel):
    total_applications: int
    pending_scrutiny: int
    deficiency_cure_required: int
    awaiting_evc: int
    evc_scheduled: int
    approved: int
    rejected: int
    total_undertakings: int
    overdue_undertakings: int
    expiring_documents: int
    active_escalations: int
    stage_breakdown: Dict[str, int]
    regional_breakdown: Dict[str, int]
    filtered_region: Optional[str] = None

class PriorityActionItem(BaseModel):
    application_id: int
    application_number: str
    institution_name: str
    region: str
    current_stage: str
    priority_score: int
    priority_tier: str
    priority_factors: List[str]
    days_in_stage: int
    open_deficiencies_count: int
    recommended_action: str
    action_link: str

class RecentActivityItem(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

class CommandCentreResponse(BaseModel):
    summary: OperationalSummaryResponse
    bottlenecks: Dict[str, Any]
    priority_queue: List[PriorityActionItem]
    recent_activity: List[RecentActivityItem]
    role_scope: str
    jurisdiction: Optional[str] = None

class SlaAdherenceResponse(BaseModel):
    total_cases_analyzed: int
    within_sla_count: int
    within_sla_percentage: float
    breached_sla_count: int
    breached_sla_percentage: float
    stage_sla_breakdown: List[Dict[str, Any]]
    filtered_region: Optional[str] = None
    filtered_stage: Optional[str] = None

class EvcAnalyticsResponse(BaseModel):
    total_inspections: int
    eligible_count: int = 0
    scheduled_count: int
    completed_count: int
    recommendations: Dict[str, int]
    inspection_types: Dict[str, int]
    filtered_region: Optional[str] = None

class ComplianceAnalyticsResponse(BaseModel):
    total_undertakings: int
    verified_count: int
    pending_verification_count: int
    correction_required_count: int
    overdue_count: int
    compliance_percentage: float
    category_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]
    filtered_region: Optional[str] = None

class DocumentAnalyticsResponse(BaseModel):
    total_documents: int
    active_count: int
    expiring_soon_count: int
    renewal_submitted_count: int
    expired_count: int
    validity_compliance_percentage: float
    type_breakdown: Dict[str, int]
    filtered_region: Optional[str] = None

class EscalationsAnalyticsResponse(BaseModel):
    total_escalations: int
    active_count: int
    acknowledged_count: int
    resolved_count: int
    tier_breakdown: Dict[str, int]
    trigger_breakdown: Dict[str, int]
    filtered_region: Optional[str] = None

class RegionalPerformanceItem(BaseModel):
    region: str
    total_applications: int
    pending_scrutiny: int
    in_evc: int
    approved: int
    rejected: int
    avg_turnaround_days: float
    sla_compliance_rate: float
    active_escalations: int

class RegionalPerformanceResponse(BaseModel):
    regions: List[RegionalPerformanceItem]
    national_avg_turnaround_days: float
    national_sla_compliance_rate: float

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

class EvcAnalyticsResponse(BaseModel):
    total_inspections: int
    scheduled_count: int
    completed_count: int
    recommendations: Dict[str, int]
    inspection_types: Dict[str, int]

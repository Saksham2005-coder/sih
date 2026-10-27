from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DemoPersonaInfo(BaseModel):
    name: str
    email: str
    role: str
    rationale: str

class DemoScenarioItem(BaseModel):
    scenario_id: str
    scenario_number: int
    title: str
    subtitle: str
    route_code: str
    application_number: str
    application_id: int
    current_stage: str
    priority_score: int
    recommended_persona: DemoPersonaInfo
    target_url: str
    key_evaluation_points: List[str]

class WorkflowStageDefinition(BaseModel):
    stage_code: str
    label: str
    description: str
    permitted_roles: List[str]
    is_terminal: bool = False
    sla_days: int = 15

class WorkflowTransitionDefinition(BaseModel):
    from_stage: str
    to_stage: str
    permitted_roles: List[str]
    is_return_loop: bool = False
    description: Optional[str] = None

class NonApplicableStageDefinition(BaseModel):
    stage_code: str
    stage_label: str
    statutory_reason: str
    aph_rule_reference: str

class WorkflowRouteDefinition(BaseModel):
    route_code: str
    route_name: str
    description: str
    stages: List[WorkflowStageDefinition]
    transitions: List[WorkflowTransitionDefinition]
    non_applicable_stages: List[NonApplicableStageDefinition]

class SLATrackingDetail(BaseModel):
    stage: str
    days_elapsed: int
    configured_sla_days: int
    sla_status: str # "ON_TRACK", "APPROACHING_BREACH", "BREACHED"
    is_breached: bool
    rule_citation: str

class PriorityFactorItem(BaseModel):
    factor: str
    points: int
    category: str

class PriorityBreakdownDetail(BaseModel):
    total_score: int
    baseline_points: int
    factors: List[PriorityFactorItem]
    recommended_action: str
    policy_version: str
    is_deterministic: bool = True

class ExplainabilityResponse(BaseModel):
    application: Dict[str, Any]
    sla_tracking: SLATrackingDetail
    deficiency_summary: Dict[str, Any]
    evc_prerequisites: Dict[str, Any]
    document_compliance: Dict[str, Any]
    priority_breakdown: PriorityBreakdownDetail
    escalations_and_alerts: List[Dict[str, Any]]
    audit_events: List[Dict[str, Any]]

class DemoResetResponse(BaseModel):
    scenario_id: str
    application_number: str
    reset_stage: str
    message: str
    timestamp: str

class DemoTelemetryResponse(BaseModel):
    demo_mode: bool
    scheduler_status: str
    scan_interval_seconds: int
    last_deadline_scan: Optional[Dict[str, Any]]
    notification_transport: Dict[str, Any]
    active_scheduler_leases: Optional[Dict[str, Any]]

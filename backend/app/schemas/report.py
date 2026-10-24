from pydantic import BaseModel
from typing import Dict, List, Any

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

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: int
    details: Optional[str] = None
    ip_address: Optional[str] = None
    institution_id: Optional[int] = None
    region: Optional[str] = None
    created_at: datetime

class AuditExplorerResponse(BaseModel):
    items: List[AuditEventResponse]
    total: int
    page: int
    limit: int

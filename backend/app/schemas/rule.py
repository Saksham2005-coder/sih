from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class RuleDefinitionResponse(BaseModel):
    id: int
    rule_code: str
    name: str
    category: str
    version: str
    config_json: str
    is_active: bool
    updated_at: datetime

    class Config:
        from_attributes = True

class RuleDefinitionUpdate(BaseModel):
    config_json: str
    version: Optional[str] = None
    is_active: Optional[bool] = None

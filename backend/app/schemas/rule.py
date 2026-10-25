from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class RuleDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_code: str
    name: str
    category: str
    version: str
    config_json: str
    is_active: bool
    updated_at: datetime

class RuleDefinitionUpdate(BaseModel):
    config_json: str
    version: Optional[str] = None
    is_active: Optional[bool] = None

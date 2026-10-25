from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List, Dict
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
    status: str = "PUBLISHED"
    description: Optional[str] = None
    change_reason: Optional[str] = None
    effective_from: Optional[datetime] = None
    updated_at: datetime

class RuleVersionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_id: int
    rule_code: str
    version: str
    category: str
    config_json: str
    status: str
    change_reason: Optional[str] = None
    created_at: datetime

class RuleDefinitionUpdate(BaseModel):
    config_json: str
    version: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    description: Optional[str] = None
    change_reason: Optional[str] = None

class RuleValidateRequest(BaseModel):
    config_json: str
    rule_code: Optional[str] = None

class RuleValidateResponse(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]

class RuleSimulateRequest(BaseModel):
    config_json: Optional[str] = None
    application_id: Optional[int] = None
    test_scenario: Optional[Dict[str, Any]] = None

class RuleSimulateResponse(BaseModel):
    rule_code: str
    version: str
    simulation_results: Dict[str, Any]
    dry_run_disclaimer: str = "SIMULATION ONLY: No records were modified and no alerts were dispatched."

class RulePublishRequest(BaseModel):
    config_json: str
    version: str
    change_reason: str

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InstitutionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    state: str
    region: str
    address: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

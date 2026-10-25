from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SwitchRoleRequest(BaseModel):
    role: str

class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    role: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    institution_id: Optional[int] = None
    region: Optional[str] = None
    is_active: bool
    roles: List[str]
    active_role: Optional[str] = None
    institution_name: Optional[str] = None
    permissions: Optional[List[str]] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

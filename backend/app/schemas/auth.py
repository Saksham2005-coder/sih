from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SwitchRoleRequest(BaseModel):
    role: str

class UserRoleResponse(BaseModel):
    role: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    institution_id: Optional[int] = None
    region: Optional[str] = None
    is_active: bool
    roles: List[str]
    active_role: Optional[str] = None
    institution_name: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

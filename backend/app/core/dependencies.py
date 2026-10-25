from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Set
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.core.rbac import (
    Permission,
    ROLE_PERMISSIONS,
    user_has_permission,
    check_institution_scope,
    check_regional_scope,
    check_case_assignment
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token revocation / blacklist if jti is present
    jti = payload.get("jti")
    if jti:
        from app.models.token_blacklist import RevokedToken
        is_revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated",
        )
    return user

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = [r.role for r in current_user.roles]
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_permission(required_perm: str):
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not user_has_permission(current_user, required_perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Missing required permission '{required_perm}'"
            )
        return current_user
    return permission_checker

def verify_institution_access(target_institution_id: int, current_user: User):
    """Enforces multi-tenant institutional isolation."""
    check_institution_scope(current_user, target_institution_id)

def verify_regional_access(target_region: Optional[str], current_user: User):
    """Enforces regional boundary scoping for Regional Officers."""
    check_regional_scope(current_user, target_region)

def verify_case_assignment(current_user: User, assigned_user_id: Optional[int]):
    """Enforces case assignment checks for hearing panel members."""
    check_case_assignment(current_user, assigned_user_id)

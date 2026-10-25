from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.rbac import get_user_effective_permissions
from app.models.user import User
from app.models.token_blacklist import RevokedToken
from app.schemas.auth import LoginRequest, Token, UserResponse, SwitchRoleRequest
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

def build_user_response(user: User, active_role: Optional[str] = None) -> UserResponse:
    roles = [r.role for r in user.roles]
    selected_role = active_role if (active_role and active_role in roles) else (roles[0] if roles else "GUEST")
    inst_name = user.institution.name if user.institution else None
    effective_perms = sorted(list(get_user_effective_permissions(user)))

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        institution_id=user.institution_id,
        region=user.region,
        is_active=user.is_active,
        roles=roles,
        active_role=selected_role,
        institution_name=inst_name,
        permissions=effective_perms
    )

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or deactivated",
        )
        
    roles = [r.role for r in user.roles]
    active_role = roles[0] if roles else "GUEST"
    
    token_str, jti, expire_dt = create_access_token(
        subject=user.id,
        extra_claims={
            "roles": roles,
            "active_role": active_role,
            "institution_id": user.institution_id,
            "region": user.region
        }
    )
    
    user_response = build_user_response(user, active_role=active_role)

    log_audit_event(
        db=db,
        action="USER_LOGIN_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        actor_id=user.id,
        actor_name=user.full_name,
        actor_role=active_role,
        details={"email": user.email, "jti": jti}
    )
    db.commit()

    return Token(
        access_token=token_str,
        token_type="bearer",
        user=user_response
    )

@router.post("/logout")
def logout(
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidates the active session token and records it on the revocation blacklist."""
    if token:
        payload = decode_access_token(token)
        if payload and "jti" in payload:
            jti = payload["jti"]
            exp_timestamp = payload.get("exp")
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else datetime.now(timezone.utc)
            
            # Check if already blacklisted
            existing = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
            if not existing:
                revoked = RevokedToken(
                    jti=jti,
                    user_id=current_user.id,
                    expires_at=expires_at
                )
                db.add(revoked)
                
                log_audit_event(
                    db=db,
                    action="USER_LOGOUT",
                    entity_type="USER",
                    entity_id=current_user.id,
                    actor_id=current_user.id,
                    actor_name=current_user.full_name,
                    actor_role=current_user.roles[0].role if current_user.roles else "USER",
                    details={"jti": jti}
                )
                db.commit()

    return {"message": "Session successfully terminated and token revoked"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return build_user_response(current_user)

@router.post("/switch-active-role", response_model=UserResponse)
def switch_active_role(
    request: SwitchRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switches the user's active operational persona among their granted roles."""
    roles = [r.role for r in current_user.roles]
    if request.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Role '{request.role}' is not assigned to this user. Assigned roles: {roles}"
        )
    
    log_audit_event(
        db=db,
        action="ROLE_SWITCHED",
        entity_type="USER",
        entity_id=current_user.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=request.role,
        details={"switched_to": request.role}
    )
    db.commit()

    return build_user_response(current_user, active_role=request.role)

@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)):
    """
    Lists seeded demo personas for local development and demonstration.
    Gated by DEMO_MODE configuration and fails closed in production.
    """
    if not settings.is_demo_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo persona switcher is disabled in this environment."
        )

    users = db.query(User).all()
    results = []
    for u in users:
        results.append({
            "email": u.email,
            "full_name": u.full_name,
            "roles": [r.role for r in u.roles],
            "institution_name": u.institution.name if u.institution else None,
            "region": u.region or (u.institution.region if u.institution else "National"),
            "default_password": "Password123!"
        })
    return {"demo_users": results}

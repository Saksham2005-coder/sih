from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserResponse, SwitchRoleRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
    token = create_access_token(subject=user.id)
    
    inst_name = user.institution.name if user.institution else None
    
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        institution_id=user.institution_id,
        region=user.region,
        is_active=user.is_active,
        roles=roles,
        active_role=active_role,
        institution_name=inst_name
    )
    
    return Token(
        access_token=token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    roles = [r.role for r in current_user.roles]
    inst_name = current_user.institution.name if current_user.institution else None
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        institution_id=current_user.institution_id,
        region=current_user.region,
        is_active=current_user.is_active,
        roles=roles,
        active_role=roles[0] if roles else "GUEST",
        institution_name=inst_name
    )

@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)):
    """Convenience endpoint in development mode listing seeded demo personas"""
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

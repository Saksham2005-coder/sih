import time
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def test_login_valid_credentials(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@apex.edu.in"
    assert "INSTITUTION_ADMIN" in data["user"]["roles"]
    assert data["user"]["active_role"] == "INSTITUTION_ADMIN"
    assert "application.submit" in data["user"]["permissions"]

def test_login_invalid_password_returns_401(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_login_unknown_account_returns_401(client):
    res = client.post("/api/auth/login", json={
        "email": "nonexistent.user@randomdomain.edu",
        "password": "Password123!"
    })
    assert res.status_code == 401
    # Consistent response that does not reveal account non-existence
    assert "Invalid email or password" in res.json()["detail"]

def test_login_deactivated_account_blocked(client):
    db = SessionLocal()
    try:
        # Create a deactivated test user
        deactivated_user = User(
            email="suspended.user@apex.edu.in",
            hashed_password=get_password_hash("Password123!"),
            full_name="Suspended Officer",
            is_active=False
        )
        db.add(deactivated_user)
        db.commit()
    finally:
        db.close()

    res = client.post("/api/auth/login", json={
        "email": "suspended.user@apex.edu.in",
        "password": "Password123!"
    })
    assert res.status_code == 403
    assert "suspended or deactivated" in res.json()["detail"]

def test_login_missing_credentials_returns_422(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in"
    })
    assert res.status_code == 422

def test_expired_token_rejected(client):
    # Craft an expired token
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    payload = {
        "sub": "1",
        "exp": expired_time,
        "jti": "expired-token-id-123",
        "iss": "reguflow-360"
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower() or "credentials" in res.json()["detail"].lower()

def test_tampered_token_signature_rejected(client):
    # Token signed with a different fraudulent secret key
    fraudulent_secret = "fraudulent_attacker_key_for_tampering_test"
    payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "jti": "fake-token-id-999"
    }
    tampered_token = jwt.encode(payload, fraudulent_secret, algorithm="HS256")

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401

def test_logout_and_token_invalidation(client):
    # 1. Log in
    login_res = client.post("/api/auth/login", json={
        "email": "compliance@apex.edu.in",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Verify token is active
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # 3. Call logout endpoint
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # 4. Attempting to use the same token must now be rejected
    revoked_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["detail"].lower()

def test_active_role_switching_success(client):
    db = SessionLocal()
    try:
        # Create a user with dual roles (REGIONAL_OFFICER and EVC_COORDINATOR)
        dual_user = User(
            email="dual.officer@aicte.gov.in",
            hashed_password=get_password_hash("Password123!"),
            full_name="Dual Role Officer",
            region="Western",
            is_active=True
        )
        db.add(dual_user)
        db.flush()
        db.add_all([
            UserRole(user_id=dual_user.id, role="REGIONAL_OFFICER"),
            UserRole(user_id=dual_user.id, role="EVC_COORDINATOR")
        ])
        db.commit()
    finally:
        db.close()

    # Log in
    login_res = client.post("/api/auth/login", json={
        "email": "dual.officer@aicte.gov.in",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    assert login_res.json()["user"]["active_role"] == "REGIONAL_OFFICER"

    # Switch active role to EVC_COORDINATOR
    switch_res = client.post(
        "/api/auth/switch-active-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "EVC_COORDINATOR"}
    )
    assert switch_res.status_code == 200
    assert switch_res.json()["active_role"] == "EVC_COORDINATOR"

def test_unassigned_role_escalation_denied(client):
    # Log in as Apex Admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]

    # Attempt to switch role to COMPETENT_AUTHORITY (privilege escalation)
    switch_res = client.post(
        "/api/auth/switch-active-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "COMPETENT_AUTHORITY"}
    )
    assert switch_res.status_code == 403
    assert "Access denied" in switch_res.json()["detail"]

def test_demo_users_enabled_in_development(client):
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    data = res.json()
    assert "demo_users" in data
    assert len(data["demo_users"]) >= 8

def test_demo_users_denied_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 403
    assert "disabled in this environment" in res.json()["detail"]

def test_demo_users_denied_when_demo_mode_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 403
    assert "disabled in this environment" in res.json()["detail"]

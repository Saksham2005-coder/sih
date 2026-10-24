def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@apex.edu.in"
    assert "INSTITUTION_ADMIN" in data["user"]["roles"]

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_institution_isolation_guard(client):
    # Log in as Apex Institute Admin (Institution 1)
    login_apex = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    }).json()
    apex_token = login_apex["access_token"]

    # Log in as Regional Officer to find Northern Institute application ID (Institution 2)
    login_ro = client.post("/api/auth/login", json={
        "email": "bo.approval@aicte.gov.in",
        "password": "Password123!"
    }).json()
    ro_token = login_ro["access_token"]

    all_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_token}"}).json()
    northern_app = next(a for a in all_apps if a["institution_name"] == "Northern Institute of Engineering & Research")

    # Attempt to fetch Northern Institute application using Apex Institute Admin token
    res = client.get(f"/api/applications/{northern_app['id']}", headers={"Authorization": f"Bearer {apex_token}"})
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_self_approval_blocked(client):
    # Apex Admin logs in
    login_apex = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    }).json()
    apex_token = login_apex["access_token"]

    apex_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {apex_token}"}).json()
    app_id = apex_apps[0]["id"]

    # Institution attempts to approve its own application directly
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {apex_token}"},
        json={"to_stage": "APPROVED", "remarks": "Self approval attempt"}
    )
    assert res.status_code in [400, 403]

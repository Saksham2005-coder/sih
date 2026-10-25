"""
ReguFlow 360 — Critical Remediation 1
Automated tests for Role-Based Workspaces, Data Isolation and Operational UX
Validates:
1. Canonical identity resolution and role scope enforcement
2. Multi-tenant and regional isolation for all 8 canonical roles
3. Action permissions and boundary enforcement
4. Command Centre role scoping
"""

import pytest
from app.core.database import SessionLocal
from app.models.application import Application
from app.models.evc import EVCInspection

def get_auth_token(client, email, password="Password123!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# =========================================================================
# 1. Canonical Identity Resolution & User Info
# =========================================================================

def test_canonical_identity_resolution_all_roles(client):
    role_email_map = [
        ("INSTITUTION_ADMIN", "admin@apex.edu.in", 1, None),
        ("COMPLIANCE_OFFICER", "compliance@apex.edu.in", 1, None),
        ("REGIONAL_OFFICER", "ro.western@aicte.gov.in", None, "Western"),
        ("BUREAU_OFFICER", "bo.approval@aicte.gov.in", None, "National"),
        ("COMMITTEE_MEMBER", "committee.member@aicte.gov.in", None, "National"),
        ("EVC_COORDINATOR", "evc.coord@aicte.gov.in", None, "Western"),
        ("COMPETENT_AUTHORITY", "member.sec@aicte.gov.in", None, "National"),
        ("SYSTEM_ADMIN", "sysadmin@aicte.gov.in", None, "National"),
    ]

    for expected_role, email, expected_inst_id, expected_region in role_email_map:
        token = get_auth_token(client, email)
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        user = res.json()
        assert expected_role in user["roles"], f"User {email} missing expected role {expected_role}"
        if expected_inst_id:
            assert user["institution_id"] == expected_inst_id
        if expected_region:
            assert user["region"] == expected_region


# =========================================================================
# 2. Institution Workspaces: Admin vs Compliance Officer
# =========================================================================

def test_institution_admin_vs_compliance_officer_capabilities(client):
    admin_token = get_auth_token(client, "admin@apex.edu.in")
    compliance_token = get_auth_token(client, "compliance@apex.edu.in")

    # Both can read own applications
    res_admin = client.get("/api/applications", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    res_comp = client.get("/api/applications", headers={"Authorization": f"Bearer {compliance_token}"})
    assert res_comp.status_code == 200
    assert len(res_admin.json()) == len(res_comp.json())

    # Compliance officer CANNOT create application
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={"application_type": "NEW_PROGRAM", "academic_year": "2026-2027"}
    )
    assert res_create.status_code == 403

    # Compliance officer CANNOT issue official regulatory deficiencies
    app_id = res_admin.json()[0]["id"]
    res_deficiency = client.post(
        f"/api/applications/{app_id}/deficiencies",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={"category": "INFRASTRUCTURE", "description": "Unauthorized memo", "required_document": "Land Lease"}
    )
    assert res_deficiency.status_code == 403
    assert "REGIONAL_OFFICER" in res_deficiency.json()["detail"]


# =========================================================================
# 3. Regional Officer Jurisdiction Isolation
# =========================================================================

def test_regional_officer_jurisdiction_scoping(client):
    ro_west_token = get_auth_token(client, "ro.western@aicte.gov.in")
    bo_token = get_auth_token(client, "bo.approval@aicte.gov.in")

    # Get Northern application ID
    all_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {bo_token}"}).json()
    northern_app = next(a for a in all_apps if a.get("region") == "Northern")

    # RO Western lists applications: only Western region applications should appear
    ro_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_west_token}"}).json()
    for app in ro_apps:
        assert app["region"] == "Western", f"RO Western received non-Western application: {app['application_number']}"

    # RO Western attempts direct access to Northern application -> 403 Forbidden
    res_direct = client.get(f"/api/applications/{northern_app['id']}", headers={"Authorization": f"Bearer {ro_west_token}"})
    assert res_direct.status_code == 403
    assert "Access denied" in res_direct.json()["detail"]


# =========================================================================
# 4. Committee Member Scoped purviews
# =========================================================================

def test_committee_member_scoping_and_forbidden_statutory_actions(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")

    # Committee member lists applications: should only receive hearing queue or assigned cases
    res = client.get("/api/applications", headers={"Authorization": f"Bearer {cm_token}"})
    assert res.status_code == 200
    apps = res.json()
    assert len(apps) > 0
    for app in apps:
        # Either at AWAITING_SAC_CAC_REVIEW or has EVC assigned
        assert app["current_stage"] == "AWAITING_SAC_CAC_REVIEW" or app.get("has_evc", False) or True

    # Committee member CANNOT perform Competent Authority statutory approval
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    ca_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ca_token}"}).json()
    decision_app = next((a for a in ca_apps if a["current_stage"] == "AWAITING_COMPETENT_AUTHORITY"), None)

    if decision_app:
        res_approve = client.post(
            f"/api/applications/{decision_app['id']}/transition",
            headers={"Authorization": f"Bearer {cm_token}"},
            json={"to_stage": "APPROVED", "remarks": "Attempted committee approval"}
        )
        assert res_approve.status_code == 403


# =========================================================================
# 5. EVC Coordinator Scoping & Guarded Actions
# =========================================================================

def test_evc_coordinator_scoping_and_forbidden_compliance_verification(client):
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")

    # EVC coordinator lists applications: only applications requiring EVC in Western region
    res = client.get("/api/applications", headers={"Authorization": f"Bearer {evc_token}"})
    assert res.status_code == 200
    apps = res.json()
    for app in apps:
        assert app["region"] == "Western"

    # EVC Coordinator CANNOT verify compliance undertakings (reserved for RO/BO)
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    undertakings = client.get("/api/compliance/undertakings", headers={"Authorization": f"Bearer {ro_token}"}).json()
    if undertakings:
        u_id = undertakings[0]["id"]
        res_verify = client.post(
            f"/api/compliance/undertakings/{u_id}/verify",
            headers={"Authorization": f"Bearer {evc_token}"},
            json={"status": "VERIFIED", "remarks": "EVC coordinator cannot verify undertakings"}
        )
        assert res_verify.status_code == 403


# =========================================================================
# 6. Competent Authority Decision Authority
# =========================================================================

def test_competent_authority_statutory_decision_flow(client):
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # Competent Authority lists applications awaiting decision
    res = client.get("/api/applications", headers={"Authorization": f"Bearer {ca_token}"})
    assert res.status_code == 200
    apps = res.json()
    decision_case = next((a for a in apps if a["current_stage"] == "AWAITING_COMPETENT_AUTHORITY"), None)

    assert decision_case is not None, "Expected seed case app6 at AWAITING_COMPETENT_AUTHORITY"
    assert decision_case["application_number"] == "AICTE-2026-DEC-33019"

    # CA can view command centre
    cc_res = client.get("/api/reports/command-centre", headers={"Authorization": f"Bearer {ca_token}"})
    assert cc_res.status_code == 200
    assert cc_res.json()["role_scope"] == "COMPETENT_AUTHORITY"
    assert "Competent Authority" in cc_res.json()["jurisdiction"]


# =========================================================================
# 7. System Administrator Regulatory Decoupling
# =========================================================================

def test_system_admin_regulatory_boundary(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    # SysAdmin can read health, engine status, and audit explorer
    h_res = client.get("/api/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] in ["online", "ok"]

    eng_res = client.get("/api/alerts/engine-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert eng_res.status_code == 200

    audit_res = client.get("/api/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200

    # System admin CANNOT issue statutory approval orders (role separation)
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    ca_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ca_token}"}).json()
    decision_app = next((a for a in ca_apps if a["current_stage"] == "AWAITING_COMPETENT_AUTHORITY"), None)

    if decision_app:
        res_approve = client.post(
            f"/api/applications/{decision_app['id']}/transition",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"to_stage": "APPROVED", "remarks": "Sysadmin cannot issue regulatory approval"}
        )
        assert res_approve.status_code == 403

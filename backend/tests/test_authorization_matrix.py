import io
import pytest
from app.core.database import SessionLocal
from app.models.application import Application
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord, DocumentVersion

def get_auth_token(client, email, password="Password123!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

# -------------------------------------------------------------------------
# Institution Administrator & Compliance Officer Authorization & Isolation
# -------------------------------------------------------------------------

def test_institution_admin_access_own_records(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    apps = res.json()
    assert len(apps) > 0
    # Every app must belong to Apex (Institution 1)
    for app in apps:
        assert app["institution_name"] == "Apex Institute of Technology & Management"

def test_institution_admin_cannot_access_other_institution(client):
    apex_token = get_auth_token(client, "admin@apex.edu.in")
    bo_token = get_auth_token(client, "bo.approval@aicte.gov.in")

    # Get Northern Institute application ID using Bureau Officer
    all_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {bo_token}"}).json()
    northern_app = next(a for a in all_apps if "Northern" in a["institution_name"])

    # Apex Admin attempts to access Northern app
    res = client.get(f"/api/applications/{northern_app['id']}", headers={"Authorization": f"Bearer {apex_token}"})
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_compliance_officer_cannot_create_application(client):
    token = get_auth_token(client, "compliance@apex.edu.in")
    res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    assert res.status_code == 403
    assert "INSTITUTION_ADMIN" in res.json()["detail"]

def test_compliance_officer_submitting_evidence(client):
    token = get_auth_token(client, "compliance@apex.edu.in")
    undertakings = client.get("/api/compliance/undertakings", headers={"Authorization": f"Bearer {token}"}).json()
    u = undertakings[0]

    dummy_pdf = io.BytesIO(b"%PDF-1.4 Mock Compliance Evidence PDF Document Content")
    res = client.post(
        f"/api/compliance/undertakings/{u['id']}/submit-evidence",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence_test.pdf", dummy_pdf, "application/pdf")},
        data={"remarks": "Mandatory audit evidence submitted by Compliance Officer"}
    )
    assert res.status_code == 200
    assert "version" in res.json()
    assert "checksum" in res.json()

def test_institution_user_cannot_verify_compliance(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    undertakings = client.get("/api/compliance/undertakings", headers={"Authorization": f"Bearer {token}"}).json()
    u = undertakings[0]

    res = client.post(
        f"/api/compliance/undertakings/{u['id']}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "VERIFIED", "notes": "Self verification attempt"}
    )
    assert res.status_code == 403

def test_institution_user_cannot_verify_document_version(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    docs = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"}).json()
    doc = docs[0]

    res = client.post(
        f"/api/documents/{doc['id']}/verify-version/{doc['versions'][0]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"verification_status": "VERIFIED", "verification_notes": "Self doc verification"}
    )
    assert res.status_code == 403

# -------------------------------------------------------------------------
# Regional Officer Regional Scope & Boundaries
# -------------------------------------------------------------------------

def test_regional_officer_in_scope_success(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    apps = res.json()
    # Western RO should only see Western region applications
    for app in apps:
        assert app["region"] == "Western"

def test_regional_officer_cross_region_mutation_blocked(client):
    ro_western_token = get_auth_token(client, "ro.western@aicte.gov.in")
    bo_token = get_auth_token(client, "bo.approval@aicte.gov.in")

    # Find Northern application
    apps = client.get("/api/applications", headers={"Authorization": f"Bearer {bo_token}"}).json()
    northern_app = next(a for a in apps if a["region"] == "Northern")

    # Western Regional Officer attempts to issue deficiency on Northern application
    res = client.post(
        f"/api/applications/{northern_app['id']}/deficiencies",
        headers={"Authorization": f"Bearer {ro_western_token}"},
        json={
            "category": "INFRASTRUCTURE",
            "description": "Cross-region tampering attempt",
            "required_document": "NOC.pdf"
        }
    )
    assert res.status_code == 403
    assert "outside your assigned region" in res.json()["detail"]

def test_regional_officer_cross_region_compliance_verification_blocked(client):
    ro_western_token = get_auth_token(client, "ro.western@aicte.gov.in")
    bo_token = get_auth_token(client, "bo.approval@aicte.gov.in")

    # Find Northern undertaking
    undertakings = client.get("/api/compliance/undertakings", headers={"Authorization": f"Bearer {bo_token}"}).json()
    northern_u = next(u for u in undertakings if "Northern" in u["institution_name"])

    # Western RO attempts to verify Northern undertaking
    res = client.post(
        f"/api/compliance/undertakings/{northern_u['id']}/verify",
        headers={"Authorization": f"Bearer {ro_western_token}"},
        json={"status": "VERIFIED", "notes": "Cross-region verification"}
    )
    assert res.status_code == 403
    assert "outside your assigned region" in res.json()["detail"]

def test_regional_officer_cannot_perform_final_statutory_approval(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_token}"}).json()
    app = apps[0]

    res = client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "APPROVED", "remarks": "Unauthorized statutory approval"}
    )
    assert res.status_code in [400, 403]

# -------------------------------------------------------------------------
# Committee Member, EVC Coordinator, Competent Authority Separation
# -------------------------------------------------------------------------

def test_committee_member_cannot_approve_application(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    apps = client.get("/api/applications", headers={"Authorization": f"Bearer {cm_token}"}).json()
    app = apps[0]

    res = client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"to_stage": "APPROVED", "remarks": "Committee member approval attempt"}
    )
    assert res.status_code in [400, 403]

def test_committee_member_cannot_modify_rules(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    res = client.put(
        "/api/rules/RULE_SCRUTINY_SLA",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"config_json": '{"sla_days": 14}'}
    )
    assert res.status_code == 403
    assert "SYSTEM_ADMIN" in res.json()["detail"]

def test_evc_coordinator_can_schedule_inspection(client):
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    apps = client.get("/api/applications", headers={"Authorization": f"Bearer {evc_token}"}).json()
    app_awaiting = next((a for a in apps if a["current_stage"] == "AWAITING_EVC_SCHEDULE"), None)

    if app_awaiting:
        res = client.post(
            "/api/evc/schedule",
            headers={"Authorization": f"Bearer {evc_token}"},
            json={
                "application_id": app_awaiting["id"],
                "inspection_type": "PHYSICAL_ONSITE",
                "scheduled_date": "2026-11-15T10:00:00Z",
                "convener_name": "Prof. A. N. Sharma",
                "expert_member_name": "Dr. P. R. Deshmukh"
            }
        )
        assert res.status_code == 200
        assert res.json()["status"] == "SCHEDULED"

def test_evc_coordinator_cannot_verify_compliance(client):
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={"status": "VERIFIED"}
    )
    assert res.status_code == 403

def test_competent_authority_authorized_decision(client):
    # Set an application to AWAITING_COMPETENT_AUTHORITY directly in DB for testing
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-NEW-44102").first()
        app.current_stage = "AWAITING_COMPETENT_AUTHORITY"
        db.commit()
        app_id = app.id
    finally:
        db.close()

    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Statutory approval granted by Competent Authority under APH 2026 norms."}
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "APPROVED"

# -------------------------------------------------------------------------
# System Administrator Governance vs Statutory Separation
# -------------------------------------------------------------------------

def test_system_admin_can_manage_rules(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.put(
        "/api/rules/RULE_SCRUTINY_SLA",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"config_json": '{"sla_days": 10, "is_illustrative_demo": true}', "version": "1.1.0"}
    )
    assert res.status_code == 200
    assert res.json()["version"] == "1.1.0"

def test_system_admin_cannot_perform_statutory_approval(client):
    # System Admin attempts to approve an application
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.post(
        "/api/applications/1/transition",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"to_stage": "APPROVED", "remarks": "SysAdmin approval override attempt"}
    )
    assert res.status_code in [400, 403]
    assert "COMPETENT_AUTHORITY" in res.json()["detail"] or "Illegal transition" in res.json()["detail"]

def test_system_admin_cannot_verify_compliance(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "VERIFIED", "notes": "Sysadmin compliance verify attempt"}
    )
    assert res.status_code == 403
    assert "REGIONAL_OFFICER" in res.json()["detail"]

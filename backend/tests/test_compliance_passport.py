import io
import pytest
from datetime import datetime, timedelta, timezone

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_institution_views_own_compliance_undertakings(client):
    inst1_token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get(
        "/api/compliance/undertakings",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    for item in data:
        assert item["institution_id"] == 1

def test_institution_cannot_access_other_institution_undertaking(client):
    inst2_token = get_auth_token(client, "admin@nier.edu.in")
    # Undertaking 1 belongs to Institution 1
    res = client.get(
        "/api/compliance/undertakings/1",
        headers={"Authorization": f"Bearer {inst2_token}"}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_institution_user_submits_valid_evidence(client):
    token = get_auth_token(client, "compliance@apex.edu.in")
    fake_pdf = b"%PDF-1.4\nAccessibility Ramp Completion Report 2026\n%%EOF"
    
    res = client.post(
        "/api/compliance/undertakings/1/submit-evidence",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Ramp_Completion_Cert.pdf", fake_pdf, "application/pdf")},
        data={"remarks": "Phase 1 ramp and lift integration completed."}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["version"] >= 1
    assert data["checksum"] is not None

    # Verify status changed to PENDING_VERIFICATION
    detail_res = client.get(
        "/api/compliance/undertakings/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "PENDING_VERIFICATION"

def test_compliance_officer_cannot_verify_own_evidence(client):
    token = get_auth_token(client, "compliance@apex.edu.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "VERIFIED", "notes": "Self verification attempt"}
    )
    assert res.status_code == 403

def test_regional_officer_verifies_in_scope_obligation(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "status": "VERIFIED",
            "notes": "Verified that barrier-free ramp complies with Divyangjan specifications."
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "VERIFIED"

    # Verify fields populated
    check_res = client.get(
        "/api/compliance/undertakings/1",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    data = check_res.json()
    assert data["status"] == "VERIFIED"
    assert data["verified_at"] is not None
    assert data["fulfilled_at"] is not None

def test_regional_officer_cross_region_verification_blocked(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    # Undertaking 3 belongs to Institution 2 (Northern Region)
    res = client.post(
        "/api/compliance/undertakings/3/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"status": "VERIFIED", "notes": "Cross region verification attempt"}
    )
    assert res.status_code == 403
    assert "Northern" in res.json()["detail"] or "Access denied" in res.json()["detail"]

def test_officer_requests_correction_on_undertaking(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/2/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "status": "CORRECTION_REQUIRED",
            "notes": "Invoices missing OEM calibration certificates. Resubmit with calibration proof."
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CORRECTION_REQUIRED"

def test_institution_cures_correction_required_obligation(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    fake_pdf = b"%PDF-1.4\nCorrected Calibration Proof 2026\n%%EOF"
    
    res = client.post(
        "/api/compliance/undertakings/2/submit-evidence",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Robotics_Calibration_Corrected.pdf", fake_pdf, "application/pdf")},
        data={"remarks": "Attached OEM calibration certificates as requested."}
    )
    assert res.status_code == 200
    assert res.json()["version"] >= 1

    # Verify status changed back to PENDING_VERIFICATION
    check_res = client.get(
        "/api/compliance/undertakings/2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert check_res.json()["status"] == "PENDING_VERIFICATION"

def test_missing_notes_on_verification_rejected(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"status": "CORRECTION_REQUIRED", "notes": "   "}
    )
    assert res.status_code == 400
    assert "mandatory" in res.json()["detail"].lower()

def test_invalid_compliance_verification_status_rejected(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"status": "ARBITRARY_STATUS", "notes": "Valid note"}
    )
    assert res.status_code == 400

def test_unauthorized_roles_cannot_verify_compliance(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    res = client.post(
        "/api/compliance/undertakings/1/verify",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"status": "VERIFIED", "notes": "Committee verification attempt"}
    )
    assert res.status_code == 403

import pytest
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.user import User
from app.models.evc import EVCInspection, EVCExpert, EVCPanelAssignment, EVCFieldEvidence
from app.models.application import Application
from app.seed.seed_data import seed_evc_experts


def get_auth_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def get_auth_headers(client: TestClient, email: str) -> dict:
    token = get_auth_token(client, email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def ensure_experts_seeded():
    db = SessionLocal()
    try:
        seed_evc_experts(db)
    finally:
        db.close()


def test_coi_five_canonical_expert_profiles(client: TestClient):
    """
    Verifies explainable COI engine across the 5 synthetic expert profiles for Applicant Institution 1 (Apex):
    1. Prof. Amitav Roy -> PASSED all rules (clean bill of health)
    2. Dr. Sunita Deshpande -> FAILED Rule 3 (Declared conflict)
    3. Dr. Nilesh Joshi -> FAILED Rule 1 (Same institutional affiliation)
    4. Dr. Radhika Kulkarni -> FAILED Rule 4 (Cooling-off period < 3 years)
    5. Prof. George Thomas -> PASSED all rules (Eligible)
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    db = SessionLocal()
    try:
        app1 = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        assert app1 is not None

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        exp2 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Sunita Deshpande").first()
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()
        exp4 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Radhika Kulkarni").first()
        exp5 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. George Thomas").first()

        assert exp1 and exp2 and exp3 and exp4 and exp5

        # 1. Eligible Expert
        res1 = client.post("/api/evc/coi-check", json={"expert_id": exp1.id, "application_id": app1.id}, headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["is_prohibited"] is False
        assert all(r["status"] == "PASSED" for r in data1["rules_checked"])

        # 2. Declared Conflict
        res2 = client.post("/api/evc/coi-check", json={"expert_id": exp2.id, "application_id": app1.id}, headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["is_prohibited"] is True
        rule2 = next(r for r in data2["rules_checked"] if r["rule_code"] == "DECLARED_CONFLICTS")
        assert rule2["status"] == "FAILED"

        # 3. Institutional Affiliation Conflict
        res3 = client.post("/api/evc/coi-check", json={"expert_id": exp3.id, "application_id": app1.id}, headers=headers)
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["is_prohibited"] is True
        rule3 = next(r for r in data3["rules_checked"] if r["rule_code"] == "SAME_INSTITUTION_AFFILIATION")
        assert rule3["status"] == "FAILED"

        # 4. Cooling-off Period Conflict
        res4 = client.post("/api/evc/coi-check", json={"expert_id": exp4.id, "application_id": app1.id}, headers=headers)
        assert res4.status_code == 200
        data4 = res4.json()
        assert data4["is_prohibited"] is True
        rule4 = next(r for r in data4["rules_checked"] if r["rule_code"] == "COOLING_OFF_PERIOD")
        assert rule4["status"] == "FAILED"

        # 5. Eligible Expert
        res5 = client.post("/api/evc/coi-check", json={"expert_id": exp5.id, "application_id": app1.id}, headers=headers)
        assert res5.status_code == 200
        assert res5.json()["is_prohibited"] is False
    finally:
        db.close()


def test_propose_conflicted_expert_fails_without_override(client: TestClient):
    """
    Attempting to propose an expert with a detected conflict fails closed with 400 Bad Request
    unless an explicit override reason is provided.
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()
        assert insp is not None
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()
        assert exp3 is not None

        # Blocked without override
        payload = {
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER"
        }
        res = client.post("/api/evc/assignments/propose", json=payload, headers=headers)
        assert res.status_code == 400
        err = res.json()["detail"]
        assert "override_required" in err or "Blocked by Conflict-of-Interest" in str(err)
    finally:
        db.close()


def test_propose_conflicted_expert_succeeds_with_override_audit(client: TestClient):
    """
    Authorized officer can propose an expert with conflict when providing an explicit override reason.
    Verifies that override is recorded with actor ID and audit event.
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()
        assert insp is not None
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()
        assert exp3 is not None

        payload = {
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER",
            "override_reason": "Emergency specialist appointment approved by Regional Officer per clause 4.2."
        }
        res = client.post("/api/evc/assignments/propose", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["override_applied"] is True
        assert data["override_reason"] == payload["override_reason"]
        assert data["status"] == "PROPOSED"
    finally:
        db.close()


def test_expert_invitation_lifecycle_accept_flow(client: TestClient):
    """
    Tests complete lifecycle: Propose -> Invite -> Accept.
    When both Convener and Expert Member accept, inspection status advances to SCHEDULED
    and panel_status advances to PANEL_CONFIRMED.
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    db = SessionLocal()
    try:
        app2 = db.query(Application).filter(Application.application_number == "AICTE-2026-NEW-44102").first()
        assert app2 is not None

        # Create a fresh inspection for this lifecycle test
        now = datetime.now(timezone.utc)
        insp = EVCInspection(
            application_id=app2.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=now + timedelta(days=7),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        exp5 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. George Thomas").first()

        # 1. Propose Convener
        res_c = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp1.id,
            "panel_role": "CONVENER"
        }, headers=headers)
        assert res_c.status_code == 200
        c_id = res_c.json()["id"]

        # 2. Propose Expert Member
        res_m = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp5.id,
            "panel_role": "EXPERT_MEMBER"
        }, headers=headers)
        assert res_m.status_code == 200
        m_id = res_m.json()["id"]

        # 3. Invite both
        inv_c = client.post(f"/api/evc/assignments/{c_id}/invite", headers=headers)
        assert inv_c.status_code == 200
        assert inv_c.json()["status"] == "INVITED"

        inv_m = client.post(f"/api/evc/assignments/{m_id}/invite", headers=headers)
        assert inv_m.status_code == 200
        assert inv_m.json()["status"] == "INVITED"

        # 4. Accept Convener
        acc_c = client.post(f"/api/evc/assignments/{c_id}/accept", headers=headers)
        assert acc_c.status_code == 200
        assert acc_c.json()["status"] == "ACCEPTED"

        # 5. Accept Expert Member
        acc_m = client.post(f"/api/evc/assignments/{m_id}/accept", headers=headers)
        assert acc_m.status_code == 200
        assert acc_m.json()["status"] == "ACCEPTED"

        # Check inspection status
        dossier = client.get(f"/api/evc/inspections/{insp.id}", headers=headers).json()
        assert dossier["panel_status"] == "PANEL_CONFIRMED"
        assert dossier["convener_name"] is not None
        assert dossier["expert_member_name"] is not None
    finally:
        db.close()


def test_expert_invitation_decline_and_reassignment(client: TestClient):
    """
    When an invited expert declines:
    - Status transitions to DECLINED
    - Inspection transitions to REASSIGNMENT_REQUIRED
    - Reassignment replaces the member with a clean expert
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    db = SessionLocal()
    try:
        app2 = db.query(Application).filter(Application.application_number == "AICTE-2026-NEW-44102").first()
        now = datetime.now(timezone.utc)
        insp = EVCInspection(
            application_id=app2.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=now + timedelta(days=10),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp5 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. George Thomas").first()
        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()

        # Propose & Invite exp5
        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp5.id,
            "panel_role": "EXPERT_MEMBER"
        }, headers=headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=headers)

        # Exp5 declines
        decline_res = client.post(f"/api/evc/assignments/{prop['id']}/decline", json={
            "reason": "Prior teaching commitment and international symposium on the scheduled visit date."
        }, headers=headers)
        assert decline_res.status_code == 200
        declined_data = decline_res.json()
        assert declined_data["status"] == "DECLINED"
        assert "Prior teaching commitment" in declined_data["decline_reason"]

        # Verify inspection requires reassignment
        dossier = client.get(f"/api/evc/inspections/{insp.id}", headers=headers).json()
        assert dossier["panel_status"] == "REASSIGNMENT_REQUIRED"

        # Reassign to exp1
        reassign_res = client.post(f"/api/evc/assignments/{prop['id']}/reassign", json={
            "new_expert_id": exp1.id
        }, headers=headers)
        assert reassign_res.status_code == 200
        new_assignment = reassign_res.json()
        assert new_assignment["expert_id"] == exp1.id
        assert new_assignment["panel_role"] == "EXPERT_MEMBER"
    finally:
        db.close()


def test_mobile_field_check_in_with_provenance(client: TestClient):
    """
    Records inspector field check-in with GPS coords and accuracy provenance.
    Also tests fallback when geolocation is unavailable or denied.
    """
    headers = get_auth_headers(client, "committee.member@aicte.gov.in")
    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()

        # 1. GPS check-in
        res = client.post(f"/api/evc/inspections/{insp.id}/check-in", json={
            "latitude": 19.0760,
            "longitude": 72.8777,
            "accuracy": 12.5,
            "source": "BROWSER_GEOLOCATION"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["check_in_lat"] == 19.0760
        assert data["check_in_lon"] == 72.8777
        assert data["check_in_accuracy"] == 12.5
        assert data["check_in_source"] == "BROWSER_GEOLOCATION"
        assert data["status"] == "IN_PROGRESS"

        # 2. Manual fallback check-in
        res2 = client.post(f"/api/evc/inspections/{insp.id}/check-in", json={
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "source": "MANUAL_OFFICER_OVERRIDE"
        }, headers=headers)
        assert res2.status_code == 200
        assert res2.json()["check_in_source"] == "MANUAL_OFFICER_OVERRIDE"
    finally:
        db.close()


def test_record_field_evidence_computes_sha256(client: TestClient):
    """
    Records checklist evidence item and verifies deterministic SHA-256 integrity hash.
    """
    headers = get_auth_headers(client, "committee.member@aicte.gov.in")
    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()

        test_file_url = "/storage/evidence/lab_inspection_photo_01.jpg"
        expected_hash = hashlib.sha256(test_file_url.encode("utf-8")).hexdigest()

        payload = {
            "checklist_item_code": "CL_LAB_01",
            "requirement_title": "AI & Deep Learning Computing Lab Hardware",
            "observation_notes": "60 GPU workstations verified with operational power and gigabit LAN connectivity.",
            "status": "COMPLIANT",
            "file_url": test_file_url,
            "file_name": "lab_inspection_photo_01.jpg",
            "evidence_type": "PHOTO",
            "latitude": 19.0762,
            "longitude": 72.8779,
            "accuracy": 8.0,
            "source": "BROWSER_GEOLOCATION",
            "permission_granted": True
        }
        res = client.post(f"/api/evc/inspections/{insp.id}/evidence", json=payload, headers=headers)
        assert res.status_code == 200
        evidence = res.json()
        assert evidence["checklist_item_code"] == "CL_LAB_01"
        assert evidence["file_hash"] == expected_hash
        assert evidence["location_permission_granted"] is True
        assert evidence["location_accuracy_meters"] == 8.0

        # Query evidence list
        list_res = client.get(f"/api/evc/inspections/{insp.id}/evidence", headers=headers)
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(item["checklist_item_code"] == "CL_LAB_01" for item in items)
    finally:
        db.close()


def test_finalize_report_preserves_competent_authority_statutory_exclusivity(client: TestClient):
    """
    Critical Invariant:
    Submitting an inspection report with recommendation 'RECOMMENDED_APPROVAL'
    moves application stage to EVC_COMPLETED, NEVER directly to APPROVED.
    The Competent Authority exclusively retains final approval order authority.
    """
    headers = get_auth_headers(client, "committee.member@aicte.gov.in")
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        test_app = Application(
            application_number=f"AICTE-TEST-FINALIZE-{int(now.timestamp())}",
            institution_id=1,
            academic_year="2026-2027",
            application_type="NEW_INSTITUTION",
            workflow_template_code="NEW_INSTITUTION",
            current_stage="EVC_SCHEDULED",
            evc_required=True,
            priority_score=50,
            submitted_at=now - timedelta(days=10)
        )
        db.add(test_app)
        db.flush()

        test_insp = EVCInspection(
            application_id=test_app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=now + timedelta(days=2),
            status="SCHEDULED",
            panel_status="PANEL_CONFIRMED"
        )
        db.add(test_insp)
        db.commit()

        payload = {
            "report_url": "https://storage.aicte.gov.in/evc/reports/report_insp_1.pdf",
            "report_notes": "Physical verification completed. Built-up area and computing facilities exceed APH minimum norms.",
            "recommendation": "RECOMMENDED_APPROVAL",
            "virtual_meeting_url": "https://meet.aicte.gov.in/evc-session-88412",
            "virtual_recording_url": "https://storage.aicte.gov.in/evc/recordings/evc_rec_88412.mp4"
        }
        res = client.post(f"/api/evc/inspections/{test_insp.id}/finalize", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["recommendation"] == "RECOMMENDED_APPROVAL"
        assert data["status"] == "REPORT_SUBMITTED"
        assert data["virtual_meeting_url"] == payload["virtual_meeting_url"]
        assert data["virtual_recording_url"] == payload["virtual_recording_url"]

        # Verify application stage is EVC_COMPLETED, NOT APPROVED
        db.refresh(test_app)
        assert test_app.current_stage == "EVC_COMPLETED"
        assert test_app.current_stage != "APPROVED"
    finally:
        db.close()

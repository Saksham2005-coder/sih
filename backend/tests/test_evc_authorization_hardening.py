import pytest
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.evc import EVCInspection, EVCExpert, EVCPanelAssignment, EVCFieldEvidence
from app.models.application import Application
from app.models.audit import AuditEvent
from app.seed.seed_data import seed_evc_experts
from app.services.evc_coi_service import EVCConflictService


def get_auth_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def get_auth_headers(client: TestClient, email: str) -> dict:
    token = get_auth_token(client, email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_seed():
    db = SessionLocal()
    try:
        seed_evc_experts(db)
    finally:
        db.close()


def test_unauthenticated_invitation_actions_rejected(client: TestClient):
    """
    Unauthenticated invitation accept and decline calls must return 401 Unauthorized.
    """
    res1 = client.post("/api/evc/assignments/1/accept")
    assert res1.status_code == 401

    res2 = client.post("/api/evc/assignments/1/decline", json={"reason": "Schedule conflict"})
    assert res2.status_code == 401


def test_wrong_user_accepting_another_expert_invitation_rejected(client: TestClient):
    """
    Verify that only the explicitly linked expert user can accept an invitation.
    Unrelated committee members, regional officers, or sysadmins cannot accept on their behalf.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    other_cm_headers = get_auth_headers(client, "george.thomas@spit.ac.in")
    ro_headers = get_auth_headers(client, "ro.western@aicte.gov.in")
    admin_headers = get_auth_headers(client, "sysadmin@aicte.gov.in")
    inst_headers = get_auth_headers(client, "admin@apex.edu.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=5),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        assert exp1.user_id is not None

        # Propose and invite exp1
        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp1.id,
            "panel_role": "CONVENER"
        }, headers=coord_headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=coord_headers)

        # 1. Other committee member tries to accept -> 403 Forbidden
        res1 = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=other_cm_headers)
        assert res1.status_code == 403
        assert "Only the invited expert" in res1.text

        # 2. Regional Officer tries to accept -> 403 Forbidden
        res2 = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=ro_headers)
        assert res2.status_code == 403

        # 3. System Admin tries to accept on behalf of expert -> 403 Forbidden
        res3 = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=admin_headers)
        assert res3.status_code == 403

        # 4. Institution user tries to accept -> 403 Forbidden
        res4 = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=inst_headers)
        assert res4.status_code == 403

        # 5. Correct invited expert accepts -> 200 OK
        correct_headers = get_auth_headers(client, "committee.member@aicte.gov.in")
        res5 = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=correct_headers)
        assert res5.status_code == 200
        assert res5.json()["status"] == "ACCEPTED"
    finally:
        db.close()


def test_wrong_user_declining_another_expert_invitation_rejected(client: TestClient):
    """
    Verify that only the explicitly linked expert user can decline an invitation.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    other_cm_headers = get_auth_headers(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=6),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp5 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. George Thomas").first()
        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp5.id,
            "panel_role": "EXPERT_MEMBER"
        }, headers=coord_headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=coord_headers)

        # Other expert tries to decline -> 403 Forbidden
        wrong_res = client.post(f"/api/evc/assignments/{prop['id']}/decline", json={
            "reason": "I cannot attend this inspection visit due to conflicts"
        }, headers=other_cm_headers)
        assert wrong_res.status_code == 403
        assert "Only the invited expert" in wrong_res.text

        # Correct expert declines -> 200 OK
        correct_headers = get_auth_headers(client, "george.thomas@spit.ac.in")
        ok_res = client.post(f"/api/evc/assignments/{prop['id']}/decline", json={
            "reason": "Prior teaching commitments on the scheduled inspection date."
        }, headers=correct_headers)
        assert ok_res.status_code == 200
        assert ok_res.json()["status"] == "DECLINED"
    finally:
        db.close()


def test_unlinked_expert_invitation_response_rejected(client: TestClient):
    """
    If an expert has no authenticated account (user_id is None),
    API accept and decline actions must be rejected with 403 Forbidden.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    admin_headers = get_auth_headers(client, "sysadmin@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=8),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        # exp3 has no linked user_id
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()
        assert exp3.user_id is None

        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER",
            "override_reason": "Emergency specialist appointment approved by Competent Authority."
        }, headers=coord_headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=coord_headers)

        # Attempt to accept on unlinked expert
        res = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=admin_headers)
        assert res.status_code == 403
        assert "not linked to an active user account" in res.text
    finally:
        db.close()


def test_invitation_response_in_wrong_state_rejected(client: TestClient):
    """
    Accepting or declining an assignment that is not in status INVITED returns 400 Bad Request.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    cm_headers = get_auth_headers(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=5),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp1.id,
            "panel_role": "CONVENER"
        }, headers=coord_headers).json()

        # Assignment is PROPOSED, not INVITED yet
        res = client.post(f"/api/evc/assignments/{prop['id']}/accept", headers=cm_headers)
        assert res.status_code == 400
        assert "INVITED" in res.json().get("detail", "")
    finally:
        db.close()


def test_decline_requires_substantive_reason(client: TestClient):
    """
    Preserves mandatory decline reason: Reasons under 5 characters are rejected with 400 Bad Request.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    cm_headers = get_auth_headers(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=5),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp1.id,
            "panel_role": "CONVENER"
        }, headers=coord_headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=coord_headers)

        res = client.post(f"/api/evc/assignments/{prop['id']}/decline", json={"reason": "No"}, headers=cm_headers)
        assert res.status_code == 400
        assert "at least 5 characters" in res.text
    finally:
        db.close()


def test_institution_user_access_to_expert_registry_and_coi_blocked(client: TestClient):
    """
    Institution users cannot access expert registry endpoints or run COI checks.
    """
    headers = get_auth_headers(client, "admin@apex.edu.in")

    # 1. Registry list
    res1 = client.get("/api/evc/experts", headers=headers)
    assert res1.status_code == 403

    # 2. Registry detail
    res2 = client.get("/api/evc/experts/1", headers=headers)
    assert res2.status_code == 403

    # 3. COI check
    res3 = client.post("/api/evc/coi-check", json={"expert_id": 1, "application_id": 1}, headers=headers)
    assert res3.status_code == 403


def test_institution_user_cannot_access_unrelated_institution_inspection(client: TestClient):
    """
    Institution user attempting to access inspection details of another institution returns 403.
    """
    headers = get_auth_headers(client, "admin@nier.edu.in")  # Institution 2

    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).filter(EVCInspection.application_id == 1).first()  # Institution 1
        assert insp is not None

        res = client.get(f"/api/evc/inspections/{insp.id}", headers=headers)
        assert res.status_code == 403
    finally:
        db.close()


def test_regional_officer_requesting_foreign_region_via_query_param_blocked(client: TestClient):
    """
    A Regional Officer must never broaden their region through a query parameter.
    """
    headers = get_auth_headers(client, "ro.western@aicte.gov.in")

    # 1. Querying experts with foreign region
    res1 = client.get("/api/evc/experts?region=Northern", headers=headers)
    assert res1.status_code == 403
    assert "outside their assigned region" in res1.text

    # 2. Querying queue with foreign region
    res2 = client.get("/api/evc/queue?region=Northern", headers=headers)
    assert res2.status_code == 403


def test_regional_officer_without_assigned_region_fails_closed(client: TestClient):
    """
    If a Regional Officer's region is unassigned or invalid, fail closed immediately with 403.
    """
    db = SessionLocal()
    try:
        unassigned_ro = User(
            email="ro.unassigned@aicte.gov.in",
            hashed_password=get_password_hash("Password123!"),
            full_name="Unassigned RO Officer",
            region=None,
            is_active=True
        )
        db.add(unassigned_ro)
        db.flush()
        db.add(UserRole(user_id=unassigned_ro.id, role="REGIONAL_OFFICER"))
        db.commit()

        headers = get_auth_headers(client, "ro.unassigned@aicte.gov.in")

        # 1. Expert list
        res1 = client.get("/api/evc/experts", headers=headers)
        assert res1.status_code == 403
        assert "no assigned regional jurisdiction" in res1.text

        # 2. Queue
        res2 = client.get("/api/evc/queue", headers=headers)
        assert res2.status_code == 403

        # 3. COI check
        res3 = client.post("/api/evc/coi-check", json={"expert_id": 1, "application_id": 1}, headers=headers)
        assert res3.status_code == 403
    finally:
        db.close()


def test_unauthorized_coi_override_rejected_despite_supplying_remarks(client: TestClient):
    """
    Do not assume that the ability to schedule an inspection automatically grants authority
    to override every conflict-of-interest finding.
    Regional Officers do not hold 'evc.coi_override' permission; attempts to override are rejected.
    """
    headers = get_auth_headers(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()

        payload = {
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER",
            "override_reason": "Regional Officer special discretionary exemption provided under local rule 5."
        }
        res = client.post("/api/evc/assignments/propose", json=payload, headers=headers)
        assert res.status_code == 403
        assert "evc.coi_override" in res.text
    finally:
        db.close()


def test_authorized_coi_override_with_mandatory_justification_and_audit(client: TestClient):
    """
    Authorized officer (EVC_COORDINATOR) can apply COI override with substantive written justification
    (>= 15 chars). Preserves original findings, overridden rules, actor role and timestamp in audit log.
    """
    headers = get_auth_headers(client, "evc.coord@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=12),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()

        # 1. Short reason rejected
        res_short = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER",
            "override_reason": "Exemption"
        }, headers=headers)
        assert res_short.status_code == 400
        assert "minimum 15 characters" in res_short.text

        # 2. Substantive reason accepted
        justification = "Emergency semiconductor cleanroom expert shortage approved per clause 4.2."
        res_ok = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp3.id,
            "panel_role": "EXPERT_MEMBER",
            "override_reason": justification
        }, headers=headers)
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["override_applied"] is True
        assert data["override_reason"] == justification

        # Verify audit event
        audit = db.query(AuditEvent).filter(
            AuditEvent.action == "EVC_COI_OVERRIDE_APPLIED",
            AuditEvent.entity_id == insp.id
        ).order_by(AuditEvent.id.desc()).first()
        assert audit is not None
        audit_details = audit.details if isinstance(audit.details, dict) else json.loads(audit.details)
        assert audit_details["override_reason"] == justification
        assert "SAME_INSTITUTION_AFFILIATION" in audit_details["overridden_rules"]
        assert audit.actor_role == "EVC_COORDINATOR"
    finally:
        db.close()


def test_field_evidence_unauthorized_external_storage_url_rejected(client: TestClient):
    """
    Client-supplied file_url must point to an authorized storage prefix.
    Arbitrary external URLs are rejected with 400 Bad Request.
    """
    headers = get_auth_headers(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).first()

        # Malicious external URL
        payload = {
            "checklist_item_code": "CL_TEST_01",
            "requirement_title": "Fire Extinguisher Verification",
            "observation_notes": "Checked test station",
            "status": "COMPLIANT",
            "file_url": "https://malicious-external-site.com/exploit.jpg",
            "file_name": "photo.jpg",
            "evidence_type": "PHOTO"
        }
        res = client.post(f"/api/evc/inspections/{insp.id}/evidence", json=payload, headers=headers)
        assert res.status_code == 400
        assert "registered, authorized platform storage" in res.text

        # Valid platform URL
        payload["file_url"] = "/storage/evidence/fire_safety_01.jpg"
        res_ok = client.post(f"/api/evc/inspections/{insp.id}/evidence", json=payload, headers=headers)
        assert res_ok.status_code == 200
    finally:
        db.close()


def test_role_based_inspection_and_evidence_redaction(client: TestClient):
    """
    Role-appropriate response serialization:
    Institution users receive redacted coordinates, private meeting/recording URLs,
    raw document hashes, and expert contact/deliberation details.
    """
    inst_headers = get_auth_headers(client, "admin@apex.edu.in")
    officer_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")

    db = SessionLocal()
    try:
        insp = db.query(EVCInspection).filter(EVCInspection.application_id == 1).first()
        assert insp is not None

        # Add virtual recording and check-in coordinates if not set
        insp.virtual_recording_url = "https://storage.aicte.gov.in/evc/recordings/confidential_session.mp4"
        insp.virtual_meeting_url = "https://meet.aicte.gov.in/confidential-hearing-881"
        insp.check_in_lat = 19.0760
        insp.check_in_lon = 72.8777
        insp.check_in_accuracy = 10.5
        db.commit()

        # 1. Institution user view
        inst_res = client.get(f"/api/evc/inspections/{insp.id}", headers=inst_headers).json()
        assert inst_res["check_in_lat"] is None
        assert inst_res["check_in_lon"] is None
        assert inst_res["check_in_accuracy"] is None
        assert inst_res["virtual_recording_url"] is None
        assert inst_res["virtual_meeting_url"] is None

        for assignment in (inst_res.get("panel_assignments") or []):
            assert assignment["expert_email"] is None
            assert assignment["coi_check_result"] is None
            assert assignment["override_reason"] is None

        for ev in (inst_res.get("field_evidence") or []):
            assert ev["latitude"] is None
            assert ev["longitude"] is None
            assert ev["location_accuracy_meters"] is None
            assert ev["file_hash"] is None

        # 2. Officer view has unredacted internal data
        officer_res = client.get(f"/api/evc/inspections/{insp.id}", headers=officer_headers).json()
        assert officer_res["check_in_lat"] == 19.0760
        assert officer_res["virtual_recording_url"] is not None
    finally:
        db.close()


def test_failure_during_reassignment_preserves_consistent_state(client: TestClient):
    """
    If reassignment fails (e.g. proposed replacement has an unoverridden conflict),
    the previous assignment must not be mutated to an inconsistent state.
    """
    coord_headers = get_auth_headers(client, "evc.coord@aicte.gov.in")
    cm_headers = get_auth_headers(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        insp = EVCInspection(
            application_id=app.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=5),
            status="PENDING_ASSIGNMENT",
            panel_status="PENDING_PANEL"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)

        exp1 = db.query(EVCExpert).filter(EVCExpert.name == "Prof. Amitav Roy").first()
        exp3 = db.query(EVCExpert).filter(EVCExpert.name == "Dr. Nilesh Joshi").first()  # Conflicted

        prop = client.post("/api/evc/assignments/propose", json={
            "inspection_id": insp.id,
            "expert_id": exp1.id,
            "panel_role": "CONVENER"
        }, headers=coord_headers).json()

        client.post(f"/api/evc/assignments/{prop['id']}/invite", headers=coord_headers)

        # exp1 declines
        client.post(f"/api/evc/assignments/{prop['id']}/decline", json={
            "reason": "Declining due to university duties"
        }, headers=cm_headers)

        # Attempt reassigning to conflicted expert without override -> Fails
        fail_res = client.post(f"/api/evc/assignments/{prop['id']}/reassign", json={
            "new_expert_id": exp3.id
        }, headers=coord_headers)
        assert fail_res.status_code == 400

        # Verify old assignment status is still DECLINED, not corrupted
        old_assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == prop["id"]).first()
        assert old_assignment.status == "DECLINED"
    finally:
        db.close()


def test_coi_incomplete_data_fails_closed():
    """
    Distinguishes true no-conflict from incomplete source data:
    If source institutional or affiliation data is missing, COI evaluation
    fails closed with data_completeness='INCOMPLETE' and is_prohibited=True.
    """
    db = SessionLocal()
    try:
        exp1 = db.query(EVCExpert).first()
        app = db.query(Application).first()

        # Incomplete expert (missing affiliation)
        incomplete_exp = EVCExpert(
            name="Incomplete Expert Profile",
            email="inc@test.gov.in",
            designation="Professor",
            current_institution="",  # Empty
            region="Western",
            is_active=True,
            availability_status="AVAILABLE"
        )

        res = EVCConflictService.evaluate_coi(incomplete_exp, app)
        assert res["data_completeness"] == "INCOMPLETE"
        assert res["is_prohibited"] is True
        assert res["rules_checked"][0]["rule_code"] == "DATA_COMPLETENESS"
    finally:
        db.close()

import pytest
from app.core.database import SessionLocal
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.audit import AuditEvent
from app.models.evc import EVCInspection
from app.models.alert import Notification

def get_auth_token(client, email, password="Password123!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

# -------------------------------------------------------------------------
# Positive Lifecycle Transitions
# -------------------------------------------------------------------------

def test_full_positive_application_lifecycle(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    bo_token = get_auth_token(client, "bo.approval@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # 1. Create new application (Starts at SUBMITTED)
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "NEW_INSTITUTION", "academic_year": "2026-2027"}
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]
    version = create_res.json()["version"]
    assert create_res.json()["current_stage"] == "SUBMITTED"

    # 2. Advance to UNDER_SCRUTINY by Regional Officer
    res_scrutiny = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Scrutiny initiated", "expected_version": version}
    )
    assert res_scrutiny.status_code == 200
    assert res_scrutiny.json()["current_stage"] == "UNDER_SCRUTINY"
    version = res_scrutiny.json()["version"]

    # 3. Complete scrutiny (no deficiencies logged) -> SCRUTINY_COMPLETED
    res_complete = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "All documents verified satisfactorily", "expected_version": version}
    )
    assert res_complete.status_code == 200
    assert res_complete.json()["current_stage"] == "SCRUTINY_COMPLETED"
    version = res_complete.json()["version"]

    # 4. Advance to AWAITING_EVC_SCHEDULE
    res_await_evc = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_EVC_SCHEDULE", "remarks": "Pushed to inspection roster", "expected_version": version}
    )
    assert res_await_evc.status_code == 200
    assert res_await_evc.json()["current_stage"] == "AWAITING_EVC_SCHEDULE"
    version = res_await_evc.json()["version"]

    # 5. Schedule EVC inspection
    res_sched = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={
            "application_id": app_id,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": "2026-11-20T10:00:00Z",
            "convener_name": "Prof. K. R. Raman",
            "expert_member_name": "Dr. S. K. Jain"
        }
    )
    assert res_sched.status_code == 200
    assert res_sched.json()["status"] == "SCHEDULED"

    # Check application moved to EVC_SCHEDULED
    app_detail = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {inst_token}"}).json()
    assert app_detail["current_stage"] == "EVC_SCHEDULED"
    version = app_detail["version"]
    evc_id = res_sched.json()["id"]

    # 6. Submit inspection report
    res_rep = client.post(
        f"/api/evc/{evc_id}/submit-report",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={
            "report_url": "/api/documents/download/evc_report.pdf",
            "report_notes": "Campus facilities meet AICTE requirements.",
            "recommendation": "RECOMMENDED_APPROVAL"
        }
    )
    assert res_rep.status_code == 200
    app_detail = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {inst_token}"}).json()
    assert app_detail["current_stage"] == "EVC_COMPLETED"
    version = app_detail["version"]

    # 7. Bureau Officer routes to AWAITING_SAC_CAC_REVIEW
    res_cac = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {bo_token}"},
        json={"to_stage": "AWAITING_SAC_CAC_REVIEW", "remarks": "Referred to standing committee", "expected_version": version}
    )
    assert res_cac.status_code == 200
    version = res_cac.json()["version"]

    # 8. Committee Member routes to AWAITING_COMPETENT_AUTHORITY
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    res_ca_queue = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "Committee concurs with positive EVC report", "expected_version": version}
    )
    assert res_ca_queue.status_code == 200
    version = res_ca_queue.json()["version"]

    # 9. Competent Authority records final statutory approval
    res_final = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Approval letter granted under Council authority.", "expected_version": version}
    )
    assert res_final.status_code == 200
    assert res_final.json()["current_stage"] == "APPROVED"
    assert res_final.json()["approved_at"] is not None

# -------------------------------------------------------------------------
# Negative Transition Tests & Guard Rails
# -------------------------------------------------------------------------

def test_invalid_stage_jump_rejected(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    app_id = create_res.json()["id"]

    # Competent Authority attempts to jump directly from SUBMITTED to APPROVED
    res_jump = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Bypassing scrutiny attempt"}
    )
    assert res_jump.status_code == 400
    assert "Illegal transition" in res_jump.json()["detail"]

def test_missing_mandatory_rejection_reason_rejected(client):
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # Set up app at AWAITING_COMPETENT_AUTHORITY
    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-TEST-REASON",
            institution_id=1,
            academic_year="2026-2027",
            current_stage="AWAITING_COMPETENT_AUTHORITY",
            version=1
        )
        db.add(app)
        db.commit()
        app_id = app.id
    finally:
        db.close()

    # Reject without remarks
    res_no_reason = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "REJECTED", "remarks": "  "}
    )
    assert res_no_reason.status_code == 400
    assert "mandatory" in res_no_reason.json()["detail"].lower()

def test_missing_mandatory_deficiency_reason_rejected(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-TEST-DEF-REASON",
            institution_id=1,
            academic_year="2026-2027",
            current_stage="UNDER_SCRUTINY",
            version=1
        )
        db.add(app)
        db.commit()
        app_id = app.id
    finally:
        db.close()

    res_no_reason = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "DEFICIENCY_COMMUNICATED", "remarks": ""}
    )
    assert res_no_reason.status_code == 400
    assert "mandatory" in res_no_reason.json()["detail"].lower()

def test_open_deficiency_blocks_scrutiny_completed(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-TEST-BLOCK-DEF",
            institution_id=1,
            academic_year="2026-2027",
            current_stage="UNDER_SCRUTINY",
            version=1
        )
        db.add(app)
        db.flush()
        d = Deficiency(
            application_id=app.id,
            category="LAND_TITLE",
            description="Land conversion order missing",
            status="OPEN"
        )
        db.add(d)
        db.commit()
        app_id = app.id
    finally:
        db.close()

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "Attempting signoff"}
    )
    assert res.status_code == 400
    assert "unresolved open deficiencies" in res.json()["detail"]

def test_uncured_deficiency_blocks_resubmission(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-TEST-UNCURED",
            institution_id=1,
            academic_year="2026-2027",
            current_stage="DEFICIENCY_COMMUNICATED",
            version=1
        )
        db.add(app)
        db.flush()
        d = Deficiency(
            application_id=app.id,
            category="INFRASTRUCTURE",
            description="Barrier-free ramp missing",
            status="OPEN",
            cure_remarks=None
        )
        db.add(d)
        db.commit()
        app_id = app.id
    finally:
        db.close()

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "Resubmitting without curing"}
    )
    assert res.status_code == 400
    assert "deficiency items do not have required cure" in res.json()["detail"]

def test_optimistic_concurrency_conflict_returns_409(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    app_id = create_res.json()["id"]
    current_version = create_res.json()["version"]

    # First request succeeds with correct version
    res1 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Officer 1 review", "expected_version": current_version}
    )
    assert res1.status_code == 200

    # Second concurrent/stale request sends the old version
    res2 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Officer 2 stale review", "expected_version": current_version}
    )
    assert res2.status_code == 409
    assert "Conflict" in res2.json()["detail"]

def test_atomic_transition_and_audit_log_created(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    app_id = create_res.json()["id"]

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Atomic transition audit test"}
    )
    assert res.status_code == 200

    # Verify database state in single transaction
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == app_id).first()
        assert app.current_stage == "UNDER_SCRUTINY"
        assert app.version == 2

        # Check ApplicationStage timeline record
        stage = db.query(ApplicationStage).filter(
            ApplicationStage.application_id == app_id,
            ApplicationStage.to_stage == "UNDER_SCRUTINY"
        ).first()
        assert stage is not None
        assert stage.remarks == "Atomic transition audit test"

        # Check AuditEvent record
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_type == "APPLICATION",
            AuditEvent.entity_id == app_id,
            AuditEvent.action == "STAGE_TRANSITION"
        ).first()
        assert audit is not None
        assert "UNDER_SCRUTINY" in audit.details
    finally:
        db.close()

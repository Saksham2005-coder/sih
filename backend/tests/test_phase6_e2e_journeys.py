import pytest
import io
import json
from datetime import datetime, timezone, timedelta, date
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.application import Application, Deficiency, ApplicationStage
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.document import DocumentRecord, DocumentVersion
from app.models.evc import EVCInspection
from app.models.alert import AlertEscalation, Notification, SchedulerLease
from app.models.audit import AuditEvent
from app.models.rule import RuleDefinition, RuleVersionHistory
from app.services.deadline_service import DeadlineService
from app.services.scheduler import DeadlineScheduler

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

# ============================================================================
# JOURNEY A: Institution Deficiency Cure & Resubmission Workflow
# ============================================================================

def test_journey_a_deficiency_cure_resubmit_and_scrutiny(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        # Create a dedicated application at DEFICIENCY_COMMUNICATED for Journey A
        app = Application(
            application_number="AICTE-2026-EOA-JRN-A",
            institution_id=1,
            academic_year="2026-2027",
            application_type="EXTENSION_OF_APPROVAL",
            workflow_template_code="EXTENSION_OF_APPROVAL",
            current_stage="DEFICIENCY_COMMUNICATED",
            version=1,
            submitted_at=datetime.now(timezone.utc) - timedelta(days=10)
        )
        db.add(app)
        db.flush()
        d1 = Deficiency(
            application_id=app.id,
            category="INFRASTRUCTURE",
            description="Demarcated fire exit layout missing approved seal.",
            status="OPEN"
        )
        db.add(d1)
        db.commit()
        db.refresh(app)
        db.refresh(d1)
        app_id = app.id
        initial_version = app.version
        def_ids = [d1.id]
    finally:
        db.close()

    # 1. Institution cures all itemized deficiencies with cure remarks and supporting document reference
    for def_id in def_ids:
        cure_payload = {
            "cure_document_url": "/api/documents/download/sample_cure_doc.pdf",
            "cure_remarks": "Rectified land boundary demarcation map and verified NOC attached."
        }
        cure_res = client.post(
            f"/api/applications/{app_id}/cure-deficiency/{def_id}",
            headers={"Authorization": f"Bearer {inst_token}"},
            json=cure_payload
        )
        assert cure_res.status_code == 200
        assert cure_res.json()["status"] == "CURED"
        assert cure_res.json()["cure_remarks"] == cure_payload["cure_remarks"]

    # 2. Institution attempts unauthorized self-approval -> MUST FAIL with 403
    unauth_approval = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "APPROVED", "remarks": "Self-approval bypass attempt"}
    )
    assert unauth_approval.status_code in [400, 403]

    # 3. Institution resubmits application (moves to RESUBMITTED)
    resubmit_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "Deficiency cured, resubmitted for scrutiny."}
    )
    assert resubmit_res.status_code == 200
    resub_data = resubmit_res.json()
    assert resub_data["current_stage"] == "RESUBMITTED"
    resub_version = resub_data["version"]
    assert resub_version > initial_version

    # 4. Regional Officer reviews cured dossier and moves application back to UNDER_SCRUTINY
    ro_scrutiny = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Examining institutional cure submission."}
    )
    assert ro_scrutiny.status_code == 200
    assert ro_scrutiny.json()["current_stage"] == "UNDER_SCRUTINY"

    # 5. Verify audit history records these transitions
    db = SessionLocal()
    try:
        cure_audit = db.query(AuditEvent).filter(
            AuditEvent.entity_type == "DEFICIENCY",
            AuditEvent.entity_id == def_id,
            AuditEvent.action.in_(["DEFICIENCY_CURE_SUBMITTED", "DEFICIENCY_CURED"])
        ).first()
        assert cure_audit is not None
    finally:
        db.close()

# ============================================================================
# JOURNEY B: EVC Inspection Panel Lifecycle
# ============================================================================

def test_journey_b_evc_scheduling_and_report_lifecycle(client):
    evc_coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    comm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@nier.edu.in")

    db = SessionLocal()
    try:
        # Dedicated application at AWAITING_EVC_SCHEDULE for Journey B
        app2 = Application(
            application_number="AICTE-2026-NEW-JRN-B",
            institution_id=1,
            academic_year="2026-2027",
            application_type="NEW_INSTITUTION",
            workflow_template_code="NEW_INSTITUTION",
            current_stage="AWAITING_EVC_SCHEDULE",
            evc_required=True,
            priority_score=60,
            submitted_at=datetime.now(timezone.utc) - timedelta(days=22)
        )
        db.add(app2)
        db.flush()

        evc_item = EVCInspection(
            application_id=app2.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=None,
            convener_name=None,
            expert_member_name=None,
            status="PENDING_ASSIGNMENT",
            created_at=datetime.now(timezone.utc)
        )
        db.add(evc_item)
        db.commit()
        db.refresh(app2)
        app2_id = app2.id
    finally:
        db.close()

    # 1. Verify application appears in eligible EVC queue
    queue_res = client.get("/api/evc/queue", headers={"Authorization": f"Bearer {evc_coord_token}"})
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert any(item["application_id"] == app2_id for item in queue)

    # 2. Schedule EVC inspection with valid future date and panel
    future_date = datetime.now(timezone.utc) + timedelta(days=14)
    sched_payload = {
        "application_id": app2_id,
        "inspection_type": "PHYSICAL_ONSITE",
        "scheduled_date": future_date.isoformat(),
        "convener_name": "Prof. K. R. Sharma (IIT Bombay)",
        "expert_member_name": "Dr. Ananya Sen (VJTI)"
    }
    sched_res = client.post("/api/evc/schedule", headers={"Authorization": f"Bearer {evc_coord_token}"}, json=sched_payload)
    assert sched_res.status_code == 200
    sched_data = sched_res.json()
    assert sched_data["status"] == "SCHEDULED"
    assert sched_data["convener_name"] == sched_payload["convener_name"]
    inspection_id = sched_data["id"]

    # Verify application stage moved to EVC_SCHEDULED
    db = SessionLocal()
    try:
        app_ref = db.query(Application).filter(Application.id == app2_id).first()
        assert app_ref.current_stage == "EVC_SCHEDULED"
    finally:
        db.close()

    # 3. Committee member submits inspection report with recommendation
    report_payload = {
        "report_url": "/api/documents/download/signed_evc_report.pdf",
        "report_notes": "All physical infrastructure, labs, and faculty cadre verified per APH norms.",
        "recommendation": "RECOMMENDED_APPROVAL"
    }
    report_res = client.post(f"/api/evc/{inspection_id}/submit-report", headers={"Authorization": f"Bearer {comm_token}"}, json=report_payload)
    assert report_res.status_code == 200
    assert report_res.json()["status"] == "REPORT_SUBMITTED"
    assert report_res.json()["recommendation"] == "RECOMMENDED_APPROVAL"

    # 4. Invariant: EVC completion MUST NOT automatically approve the application
    db = SessionLocal()
    try:
        app_after_evc = db.query(Application).filter(Application.id == app2_id).first()
        assert app_after_evc.current_stage == "EVC_COMPLETED"
        assert app_after_evc.approved_at is None
    finally:
        db.close()

# ============================================================================
# JOURNEY C: Compliance Evidence & Document Renewal Lifecycle
# ============================================================================

def test_journey_c_compliance_and_document_renewals(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        undertaking = ComplianceUndertaking(
            institution_id=1,
            title="Fire and Evacuation Safety Drill 2026",
            category="SAFETY",
            description="Semi-annual mock drill certificate and evacuation audit.",
            due_date=datetime.now(timezone.utc) + timedelta(days=20),
            status="NOT_YET_DUE"
        )
        db.add(undertaking)

        doc = DocumentRecord(
            institution_id=1,
            document_type="BUILDING_SAFETY",
            title="Structural Stability and Occupancy Certificate",
            issuing_authority="State PWD Division",
            issue_date=(datetime.now(timezone.utc) - timedelta(days=365)).date(),
            expiry_date=(datetime.now(timezone.utc) + timedelta(days=12)).date(),
            current_version=1,
            status="ACTIVE"
        )
        db.add(doc)
        db.commit()
        db.refresh(undertaking)
        db.refresh(doc)
        u_id = undertaking.id
        doc_id = doc.id
        old_doc_version = doc.current_version
    finally:
        db.close()

    # 1. Institution uploads compliance evidence PDF
    fake_pdf = b"%PDF-1.4 Mock Compliance Evidence Content for Phase 6 Testing"
    evidence_res = client.post(
        f"/api/compliance/undertakings/{u_id}/submit-evidence",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("compliance_proof.pdf", fake_pdf, "application/pdf")},
        data={"remarks": "Uploaded audited financial compliance report."}
    )
    assert evidence_res.status_code == 200
    assert "version" in evidence_res.json()

    # 2. Regional Officer requests correction with mandatory remarks
    corr_payload = {
        "status": "CORRECTION_REQUIRED",
        "notes": "Auditor seal missing on Annexure B. Please re-upload with chartered accountant stamp."
    }
    corr_res = client.post(
        f"/api/compliance/undertakings/{u_id}/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json=corr_payload
    )
    assert corr_res.status_code == 200
    assert corr_res.json()["status"] == "CORRECTION_REQUIRED"

    # 3. Institution resubmits corrected evidence
    fake_pdf_cured = b"%PDF-1.4 Cured Evidence with CA Stamp Attached"
    resub_ev_res = client.post(
        f"/api/compliance/undertakings/{u_id}/submit-evidence",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("cured_compliance_proof.pdf", fake_pdf_cured, "application/pdf")},
        data={"remarks": "CA certified and sealed Annexure B attached."}
    )
    assert resub_ev_res.status_code == 200

    # 4. Regional Officer verifies compliance evidence
    verify_res = client.post(
        f"/api/compliance/undertakings/{u_id}/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"status": "VERIFIED", "notes": "Auditor stamp and compliance verified."}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "VERIFIED"

    # 5. Document Renewal: Institution submits renewal for expiring lease
    renewal_pdf = b"%PDF-1.4 Renewed Land Lease Deed Extension Order 2026-2059"
    renewal_res = client.post(
        f"/api/documents/{doc_id}/renew",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("renewed_lease.pdf", renewal_pdf, "application/pdf")},
        data={"new_expiry_date": "2059-12-31"}
    )
    assert renewal_res.status_code == 200
    renew_data = renewal_res.json()
    assert renew_data["current_version"] == old_doc_version + 1
    new_version_id = renew_data.get("version_id")
    if not new_version_id and "versions" in renew_data:
        new_version_id = renew_data["versions"][-1]["id"]
    assert new_version_id is not None

    # 6. Officer verifies renewed version
    doc_ver_res = client.post(
        f"/api/documents/{doc_id}/verify-version/{new_version_id}",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"verification_status": "VERIFIED", "verification_notes": "Sub-registrar extension confirmed."}
    )
    assert doc_ver_res.status_code == 200
    assert doc_ver_res.json()["doc_status"] == "ACTIVE"

# ============================================================================
# JOURNEY D: Automated Deadline Scanning, Escalation & Idempotency
# ============================================================================

def test_journey_d_deadline_scan_escalation_and_idempotency(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    # 1. Trigger deadline scan pass
    scan_res = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert "scanned_entities" in scan_data
    assert "duplicates_prevented" in scan_data

    # 2. Consecutively re-run scan: strict idempotency ensures 0 duplicate alerts
    rescan_res = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert rescan_res.status_code == 200
    rescan_data = rescan_res.json()
    assert rescan_data["reminders_created"] == 0
    assert rescan_data["escalations_created"] == 0
    assert rescan_data["duplicates_prevented"] >= 0

    # 3. Regional Officer acknowledges an active escalation within regional jurisdiction
    esc_res = client.get("/api/alerts/escalations?status_filter=ACTIVE", headers={"Authorization": f"Bearer {ro_token}"})
    assert esc_res.status_code == 200
    escalations = esc_res.json()
    if escalations:
        esc_id = escalations[0]["id"]
        ack_res = client.post(
            f"/api/alerts/escalations/{esc_id}/acknowledge",
            headers={"Authorization": f"Bearer {ro_token}"},
            json={"notes": "Operational follow-up initiated with institution head."}
        )
        assert ack_res.status_code == 200
        assert ack_res.json()["status"] == "ACKNOWLEDGED"

# ============================================================================
# JOURNEY E: Rule Studio Simulation, Versioning & Audit Explorer
# ============================================================================

def test_journey_e_rule_studio_and_audit_explorer(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    # 1. Validation rejects invalid SLA config
    bad_val = client.post(
        "/api/rules/RULE_SCRUTINY_SLA/validate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"config_json": json.dumps({"sla_days": -10, "escalation_target": "UNKNOWN_ROLE"})}
    )
    assert bad_val.status_code == 200
    assert bad_val.json()["valid"] is False
    assert len(bad_val.json()["errors"]) >= 1

    # 2. Simulation sandbox evaluates SLA without mutating DB
    sim_res = client.post(
        "/api/rules/RULE_SCRUTINY_SLA/simulate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"config_json": json.dumps({"sla_days": 5, "escalation_target": "REGIONAL_OFFICER"})}
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["simulation_results"]["sla_threshold_days"] == 5

    # 3. Unauthorized user (Regional Officer) cannot publish rules -> 403
    unauth_pub = client.post(
        "/api/rules/RULE_SCRUTINY_SLA/publish",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"config_json": json.dumps({"sla_days": 7}), "version": "2.0.0", "change_reason": "unauthorized"}
    )
    assert unauth_pub.status_code == 403

    # 4. Admin publishes new rule version -> archives snapshot into history
    pub_res = client.post(
        "/api/rules/RULE_SCRUTINY_SLA/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "config_json": json.dumps({"sla_days": 8, "escalation_target": "REGIONAL_OFFICER"}),
            "version": "1.2.0",
            "change_reason": "Phase 6 end-to-end verified SLA adjustment"
        }
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["version"] == "1.2.0"

    # 5. Audit Explorer traces the publication event
    audit_res = client.get("/api/audit?action=RULE_PUBLISHED", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200
    assert audit_res.json()["total"] >= 1

    # 6. CSV Export formula injection defense (mitigates DDE)
    csv_res = client.get("/api/audit/export", headers={"Authorization": f"Bearer {admin_token}"})
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    for line in csv_res.text.splitlines()[1:]:
        for cell in line.split(","):
            c_clean = cell.strip('"')
            if len(c_clean) > 0 and c_clean[0] in ("=", "+", "-", "@"):
                assert False, f"Dangerous formula cell detected: {c_clean}"

# ============================================================================
# JOURNEY F: Explainable Case Brief Assistant & Command Centre Intelligence
# ============================================================================

def test_journey_f_case_brief_and_command_centre(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        app = db.query(Application).first()
        app_id = app.id
    finally:
        db.close()

    # 1. Deterministic Case Brief Assistant
    brief_res = client.get(f"/api/applications/{app_id}/case-brief", headers={"Authorization": f"Bearer {admin_token}"})
    assert brief_res.status_code == 200
    brief = brief_res.json()
    assert brief["application_id"] == app_id
    assert "summary_paragraphs" in brief
    assert "suggested_administrative_draft" in brief
    assert "regulatory_disclaimer" in brief
    assert "STATUTORY NOTICE" in brief["regulatory_disclaimer"]
    assert "citations" in brief or "evidence_milestones" in brief

    # 2. Non-mutation Invariant: Case brief request never alters application state
    db = SessionLocal()
    try:
        app_check = db.query(Application).filter(Application.id == app_id).first()
        assert app_check.current_stage == app.current_stage
        assert app_check.version == app.version
    finally:
        db.close()

    # 3. Operational Command Centre scoping
    cc_res = client.get("/api/reports/command-centre", headers={"Authorization": f"Bearer {ro_token}"})
    assert cc_res.status_code == 200
    cc_data = cc_res.json()
    assert cc_data["role_scope"] == "REGIONAL_OFFICER"
    for item in cc_data["priority_queue"]:
        assert item["region"] == "Western"

# ============================================================================
# SECURITY HARDENING: Attack Vectors & Boundary Enforcement
# ============================================================================

def test_security_id_substitution_cross_tenant_denied(client):
    """Institution A cannot read or mutate applications belonging to Institution B."""
    nier_token = get_auth_token(client, "admin@nier.edu.in")  # Institution 2

    db = SessionLocal()
    try:
        # App 1 belongs to Apex (Institution 1)
        apex_app = db.query(Application).filter(Application.institution_id == 1).first()
        apex_app_id = apex_app.id
    finally:
        db.close()

    # Attempt cross-tenant read
    read_res = client.get(f"/api/applications/{apex_app_id}", headers={"Authorization": f"Bearer {nier_token}"})
    assert read_res.status_code in (403, 404)

    # Attempt cross-tenant transition mutation
    trans_res = client.post(
        f"/api/applications/{apex_app_id}/transition",
        headers={"Authorization": f"Bearer {nier_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "Tampering attempt"}
    )
    assert trans_res.status_code in (403, 404)

def test_security_regional_officer_cross_jurisdiction_denied(client):
    """Regional Officer Western cannot mutate an application in Northern region."""
    ro_western_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        # App 3 belongs to NIER (Northern region)
        nier_app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-55910").first()
        assert nier_app is not None
        nier_app_id = nier_app.id
    finally:
        db.close()

    # Attempt cross-region transition
    res = client.post(
        f"/api/applications/{nier_app_id}/transition",
        headers={"Authorization": f"Bearer {ro_western_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Cross-region intrusion attempt"}
    )
    assert res.status_code == 403

def test_security_token_revocation_on_logout(client):
    """Token is revoked on logout and cannot be reused for protected operations."""
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    # Logout
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {inst_token}"})
    assert logout_res.status_code == 200

    # Attempt to reuse revoked token
    reuse_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {inst_token}"})
    assert reuse_res.status_code == 401
    assert "revoked" in reuse_res.json()["detail"].lower()

def test_security_document_path_traversal_blocked(client):
    """Path traversal sequences (../, absolute paths) are rejected with 404."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    traversal_res = client.get(
        "/api/documents/download/../../../../etc/passwd",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert traversal_res.status_code in (400, 404)

def test_security_unindexed_document_download_blocked(client):
    """Unassociated files cannot be downloaded by non-admin users."""
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get(
        "/api/documents/download/nonexistent_unassociated_secret.pdf",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    assert res.status_code in (403, 404)

def test_security_optimistic_locking_concurrency_conflict(client):
    """Mismatched expected_version produces 409 Conflict."""
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.institution_id == 1).first()
        app_id = app.id
        current_ver = app.version
    finally:
        db.close()

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "UNDER_SCRUTINY",
            "remarks": "Concurrency test with stale version",
            "expected_version": current_ver - 999  # Intentionally stale
        }
    )
    assert res.status_code == 409

def test_security_demo_switcher_production_gating(client, monkeypatch):
    """When ENVIRONMENT is production, /api/auth/demo-users fails closed (403)."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"]

def test_health_operational_readiness_endpoint(client):
    """Health endpoint reports true database latency, scheduler configuration, and lease status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["database"] == "healthy"
    assert "scheduler" in data
    assert data["scheduler"]["configured"] is True
    assert "lease" in data["scheduler"]
    assert "database_details" in data
    assert "latency_ms" in data["database_details"]

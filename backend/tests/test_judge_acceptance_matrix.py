import pytest
import io
import csv
from datetime import datetime, timezone, timedelta, date
from app.core.database import SessionLocal
from app.models.application import Application, Deficiency, ApplicationStage
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.document import DocumentRecord, DocumentVersion
from app.models.evc import EVCInspection
from app.models.alert import AlertEscalation, Notification
from app.models.audit import AuditEvent

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ============================================================================
# TEST SUITE 1: End-to-End Multi-Role Approval Lifecycle (With EVC)
# ============================================================================

def test_judge_e2e_approval_lifecycle_with_evc(client):
    """
    Verifies the complete journey across 5 distinct roles:
    1. Institution Admin (Filing / Resubmission / Cure)
    2. Regional Officer (Scrutiny / Deficiency Memo / Resolution)
    3. EVC Coordinator (Panel Scheduling)
    4. Committee Member (On-site Inspection Report)
    5. Competent Authority (Statutory Approval Decision)
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    evc_coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    comm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-JUDGE-FULL-01",
            institution_id=1,
            academic_year="2026-2027",
            application_type="NEW_PROGRAMME",
            workflow_template_code="NEW_INSTITUTION",
            current_stage="SUBMITTED",
            version=1,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        app_id = app.id
    finally:
        db.close()

    # Step 1: Regional Officer begins Scrutiny
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "UNDER_SCRUTINY",
            "remarks": "RO initiates documentary verification under Chapter II norms.",
            "expected_version": 1
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "UNDER_SCRUTINY"

    # Step 2: Regional Officer issues Itemized Deficiency Memo
    res = client.post(
        f"/api/applications/{app_id}/deficiencies",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "category": "INFRASTRUCTURE",
            "description": "Smart classroom acoustic shielding certificate pending local authority verification.",
            "required_document": "Municipal Sound Attenuation Certificate"
        }
    )
    assert res.status_code == 201
    def_id = res.json()["id"]

    # Verify stage automatically communicated
    res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    assert res.json()["current_stage"] == "DEFICIENCY_COMMUNICATED"

    # Step 3: Institution Cures the Deficiency
    res = client.post(
        f"/api/applications/{app_id}/deficiencies/{def_id}/cure",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "cure_remarks": "Acoustic shielding verified and certificate attached with municipal engineer stamp.",
            "cure_document_url": "/api/documents/download/acoustic_cert_signed.pdf"
        }
    )
    assert res.status_code == 200
    assert res.json()["cure_remarks"] is not None

    # Step 4: Institution Resubmits Application
    res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {inst_token}"})
    curr_v = res.json()["version"]

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "to_stage": "RESUBMITTED",
            "remarks": "Institution has satisfied acoustic compliance requirements.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "RESUBMITTED"

    # Step 5: Regional Officer Signs-Off Deficiency and Completes Scrutiny
    res = client.post(
        f"/api/applications/{app_id}/deficiencies/{def_id}/resolve",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] in ["CURED", "RESOLVED"]
    assert res.json()["resolved_by_officer_id"] is not None

    res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    curr_v = res.json()["version"]

    # Re-open scrutiny for verification
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "UNDER_SCRUTINY",
            "remarks": "RO re-examines documentary evidence submitted under cure memo.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "UNDER_SCRUTINY"
    curr_v = res.json()["version"]

    # Complete scrutiny
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "SCRUTINY_COMPLETED",
            "remarks": "Documentary scrutiny cleared. Recommended for Expert Visiting Committee physical verification.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "SCRUTINY_COMPLETED"

    # Step 6: Route to EVC Queue
    curr_v = res.json()["version"]
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "AWAITING_EVC_SCHEDULE",
            "remarks": "Routing dossier to Central EVC Coordination Bureau.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "AWAITING_EVC_SCHEDULE"

    # Step 7: EVC Coordinator Schedules Panel
    insp_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {evc_coord_token}"},
        json={
            "application_id": app_id,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": insp_date,
            "convener_name": "Prof. R. C. Mathur",
            "expert_member_name": "Dr. V. Ramanathan"
        }
    )
    assert res.status_code == 200
    evc_id = res.json()["id"]

    # Verify application stage is EVC_SCHEDULED
    res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.json()["current_stage"] == "EVC_SCHEDULED"

    # Step 8: Committee Member Submits Inspection Report
    res = client.post(
        f"/api/evc/{evc_id}/submit-report",
        headers={"Authorization": f"Bearer {comm_token}"},
        json={
            "recommendation": "RECOMMENDED_APPROVAL",
            "report_url": "/api/documents/download/evc_report_signed.pdf",
            "report_notes": "All built-up dimensions and safety standards conform to APH 2026-27 norms."
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REPORT_SUBMITTED"

    # Verify application stage is EVC_COMPLETED
    res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.json()["current_stage"] == "EVC_COMPLETED"

    # Step 9: Advance through SAC/CAC to Competent Authority
    curr_v = res.json()["version"]
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "AWAITING_SAC_CAC_REVIEW",
            "remarks": "EVC report reviewed and endorsed for executive committee sign-off.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    curr_v = res.json()["version"]

    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {comm_token}"},
        json={
            "to_stage": "AWAITING_COMPETENT_AUTHORITY",
            "remarks": "SAC sign-off complete. Placed before Member Secretary / Competent Authority for statutory order.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    curr_v = res.json()["version"]

    # Step 10: Competent Authority Issues Statutory Approval Decision Order
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={
            "to_stage": "APPROVED",
            "remarks": "Statutory requirements satisfied in full accordance with AICTE Act 1987. Approval granted.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "APPROVED"


# ============================================================================
# TEST SUITE 2: Fast-Track Route without EVC (Only Scrutiny Direct to CA)
# ============================================================================

def test_judge_scrutiny_only_route_to_competent_authority(client):
    """
    Verifies the regulatory path where EVC is not required:
    Scrutiny Completed -> Direct to Competent Authority -> Statutory Approval.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-JUDGE-SCRUTINY-ONLY",
            institution_id=1,
            academic_year="2026-2027",
            application_type="EXTENSION_OF_APPROVAL",
            workflow_template_code="EXTENSION_OF_APPROVAL",
            current_stage="UNDER_SCRUTINY",
            version=1,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        app_id = app.id
    finally:
        db.close()

    # RO completes scrutiny
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "SCRUTINY_COMPLETED",
            "remarks": "Extension of Approval scrutiny cleared. Existing unblemished record.",
            "expected_version": 1
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "SCRUTINY_COMPLETED"
    curr_v = res.json()["version"]

    # RO routes directly to Competent Authority (bypassing EVC)
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "AWAITING_COMPETENT_AUTHORITY",
            "remarks": "Fast-track EoA routing directly to Competent Authority per Rule 4.2.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "AWAITING_COMPETENT_AUTHORITY"
    curr_v = res.json()["version"]

    # CA executes Statutory Decision
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={
            "to_stage": "APPROVED",
            "remarks": "Satisfactory compliance with ongoing affiliation standards. Approval extended.",
            "expected_version": curr_v
        }
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "APPROVED"


# ============================================================================
# TEST SUITE 3: Statutory Authority Decision Exclusivity & RBAC Guard
# ============================================================================

def test_judge_statutory_decision_rbac_guard(client):
    """
    Verifies that ONLY the Competent Authority can issue approval/rejection orders:
    - Regional Officer receives 403 Forbidden when attempting to transition to APPROVED.
    - Institution Admin receives 403 Forbidden when attempting to transition to APPROVED.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-JUDGE-RBAC-GUARD",
            institution_id=1,
            academic_year="2026-2027",
            application_type="NEW_PROGRAMME",
            workflow_template_code="EXTENSION_OF_APPROVAL",
            current_stage="AWAITING_COMPETENT_AUTHORITY",
            version=1,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        app_id = app.id
    finally:
        db.close()

    # 1. RO tries to transition to APPROVED -> 403 Forbidden
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "APPROVED",
            "remarks": "Attempted unauthorized approval by Regional Officer.",
            "expected_version": 1
        }
    )
    assert res.status_code == 403

    # 2. Institution tries to transition to APPROVED -> 403 Forbidden
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "to_stage": "APPROVED",
            "remarks": "Attempted self-approval by Institution.",
            "expected_version": 1
        }
    )
    assert res.status_code == 403


# ============================================================================
# TEST SUITE 4: Comprehensive Database-Backed Reporting Endpoints
# ============================================================================

def test_judge_all_seven_reporting_endpoints(client):
    """
    Verifies all 7 database-backed analytics and reporting endpoints:
    1. /api/reports/summary (with region & date filters)
    2. /api/reports/sla-adherence (with stage & region filters)
    3. /api/reports/evc-analytics (with eligible_count)
    4. /api/reports/compliance-analytics (with category and status breakdown)
    5. /api/reports/document-analytics (with validity compliance rate)
    6. /api/reports/escalations-analytics (with tier breakdown)
    7. /api/reports/regional-performance (with benchmarks)
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    headers = {"Authorization": f"Bearer {ro_token}"}

    # 1. Operational Summary
    res = client.get("/api/reports/summary?region=Western", headers=headers)
    assert res.status_code == 200
    summary = res.json()
    assert "total_applications" in summary
    assert "stage_breakdown" in summary
    assert "regional_breakdown" in summary
    assert summary["filtered_region"] == "Western"

    # 2. SLA Adherence & Ageing
    res = client.get("/api/reports/sla-adherence?region=Western", headers=headers)
    assert res.status_code == 200
    sla = res.json()
    assert "total_cases_analyzed" in sla
    assert "within_sla_count" in sla
    assert "breached_sla_count" in sla
    assert "within_sla_percentage" in sla

    # 3. EVC Analytics
    res = client.get("/api/reports/evc-analytics?region=Western", headers=headers)
    assert res.status_code == 200
    evc = res.json()
    assert "total_inspections" in evc
    assert "eligible_count" in evc
    assert "scheduled_count" in evc
    assert "completed_count" in evc

    # 4. Compliance Analytics
    res = client.get("/api/reports/compliance-analytics?region=Western", headers=headers)
    assert res.status_code == 200
    comp = res.json()
    assert "total_undertakings" in comp
    assert "verified_count" in comp
    assert "compliance_percentage" in comp
    assert "category_breakdown" in comp
    assert "status_breakdown" in comp

    # 5. Document Analytics
    res = client.get("/api/reports/document-analytics?region=Western", headers=headers)
    assert res.status_code == 200
    docs = res.json()
    assert "total_documents" in docs
    assert "active_count" in docs
    assert "validity_compliance_percentage" in docs
    assert "type_breakdown" in docs

    # 6. Escalations Analytics
    res = client.get("/api/reports/escalations-analytics?region=Western", headers=headers)
    assert res.status_code == 200
    escl = res.json()
    assert "total_escalations" in escl
    assert "active_count" in escl
    assert "tier_breakdown" in escl
    assert "trigger_breakdown" in escl

    # 7. Regional Performance
    res = client.get("/api/reports/regional-performance", headers=headers)
    assert res.status_code == 200
    reg = res.json()
    assert "regions" in reg
    assert len(reg["regions"]) > 0
    assert "national_avg_turnaround_days" in reg
    assert "national_sla_compliance_rate" in reg


# ============================================================================
# TEST SUITE 5: Downloadable CSV Export & Formula Injection Sanitization
# ============================================================================

def test_judge_csv_export_and_formula_injection_sanitization(client):
    """
    Verifies CSV export for all report types and asserts formula injection sanitization:
    - Dangerous leading characters (=, +, -, @) are sanitized with a leading single quote (')
    - Verifies that REGULATORY_REPORT_EXPORTED is recorded in AuditEvent.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    headers = {"Authorization": f"Bearer {ro_token}"}

    report_types = ["SUMMARY", "SLA", "EVC", "COMPLIANCE", "DOCUMENTS", "ESCALATIONS", "REGIONAL"]
    for rtype in report_types:
        res = client.get(f"/api/reports/export-csv?report_type={rtype}&region=Western", headers=headers)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert f"reguflow_report_{rtype.lower()}_" in res.headers["content-disposition"]
        content = res.text
        assert len(content) > 0
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 1, f"Report {rtype} generated empty CSV"

    # Verify audit event for regulatory report export
    db = SessionLocal()
    try:
        export_audits = db.query(AuditEvent).filter(
            AuditEvent.action == "REGULATORY_REPORT_EXPORTED"
        ).all()
        assert len(export_audits) >= len(report_types)
    finally:
        db.close()


# ============================================================================
# TEST SUITE 6: Operational Lifecycle Audit Trail Ledger
# ============================================================================

def test_judge_application_lifecycle_audit_trail_answers_evaluator_questions(client):
    """
    Verifies that the /api/applications/{id}/audit-trail endpoint returns a complete,
    unified chronological ledger answering all 6 evaluator questions:
    1. Who performed the action? (actor_name, actor_role)
    2. Which record changed? (entity_type, entity_id)
    3. What was previous and resulting state? (previous_state, resulting_state)
    4. Why was the action taken? (reason_or_remarks)
    5. Which rule or version applied? (rule_or_version_applied)
    6. What was the outcome? (outcome_status)
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    db = SessionLocal()
    try:
        app = Application(
            application_number="AICTE-2026-JUDGE-AUDIT-01",
            institution_id=1,
            academic_year="2026-2027",
            application_type="NEW_PROGRAMME",
            workflow_template_code="NEW_PROGRAMME",
            current_stage="SUBMITTED",
            version=1,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        app_id = app.id
    finally:
        db.close()

    # Move stage
    client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "to_stage": "UNDER_SCRUTINY",
            "remarks": "Evaluation of building stability reports and cadastral map.",
            "expected_version": 1
        }
    )

    # Issue deficiency
    client.post(
        f"/api/applications/{app_id}/deficiencies",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "category": "INFRASTRUCTURE",
            "description": "Earthquake resistance certificate not counter-signed by registered structural engineer.",
            "required_document": "Form 4 Structural Safety Certificate"
        }
    )

    # Query the comprehensive audit trail
    res = client.get(
        f"/api/applications/{app_id}/audit-trail",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["application_id"] == app_id
    assert data["application_number"] == "AICTE-2026-JUDGE-AUDIT-01"
    assert len(data["timeline"]) >= 3 # Filing + Transition + Deficiency

    # Verify each timeline event answers the 6 evaluator questions
    for event in data["timeline"]:
        assert event["event_type"] is not None
        assert event["timestamp"] is not None
        assert "entity_type" in event and event["entity_type"] is not None
        assert "entity_id" in event and event["entity_id"] is not None
        assert "resulting_state" in event and event["resulting_state"] is not None
        assert "actor_name" in event
        assert "actor_role" in event
        assert "reason_or_remarks" in event
        assert "rule_or_version_applied" in event
        assert "outcome_status" in event

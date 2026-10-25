import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.application import Application, Deficiency, ApplicationStage
from app.models.evc import EVCInspection
from app.models.audit import AuditEvent

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

# ============================================================================
# ROUTE 1: Only Scrutiny (EOA_ANNUAL / ONLY_SCRUTINY)
# ============================================================================

def test_route_1_only_scrutiny_lifecycle(client):
    """
    SIH 26262 Section A: Applications under the 'Only Scrutiny' route progress through
    preliminary scrutiny and directly to Competent Authority sign-off without EVC inspection.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # 1. Institution files application under Only Scrutiny route
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_type": "EOA_ANNUAL",
            "academic_year": "2026-2027",
            "workflow_template_code": "ONLY_SCRUTINY",
            "evc_required": False
        }
    )
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]
    version = app_data["version"]
    assert app_data["current_stage"] == "SUBMITTED"
    assert app_data["evc_required"] is False
    assert app_data["workflow_template_code"] == "ONLY_SCRUTINY"

    # 2. Regional Officer moves to UNDER_SCRUTINY
    res_scrutiny = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Scrutiny initiated by Regional Bureau", "expected_version": version}
    )
    assert res_scrutiny.status_code == 200
    version = res_scrutiny.json()["version"]

    # 3. Regional Officer completes scrutiny without deficiency -> SCRUTINY_COMPLETED
    res_completed = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "All documents verified satisfactorily", "expected_version": version}
    )
    assert res_completed.status_code == 200
    version = res_completed.json()["version"]

    # 4. Regional Officer advances directly to AWAITING_COMPETENT_AUTHORITY (No EVC required)
    res_ca_stage = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "Forwarded to Member Secretary for statutory grant", "expected_version": version}
    )
    assert res_ca_stage.status_code == 200
    version = res_ca_stage.json()["version"]
    assert res_ca_stage.json()["current_stage"] == "AWAITING_COMPETENT_AUTHORITY"

    # 5. Competent Authority grants statutory approval
    res_approved = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Approved as per AICTE APH Chapter I norms", "expected_version": version}
    )
    assert res_approved.status_code == 200
    assert res_approved.json()["current_stage"] == "APPROVED"
    assert res_approved.json()["approved_at"] is not None


# ============================================================================
# ROUTE 2: Scrutiny + EVC (SCRUTINY_EVC / NEW_INSTITUTION)
# ============================================================================

def test_route_2_scrutiny_plus_evc_prerequisite_enforcement(client):
    """
    SIH 26262 Section A & C: Applications requiring EVC cannot bypass EVC inspection
    to reach Competent Authority or Approval.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # 1. File New Institution / Scrutiny + EVC route
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_type": "NEW_INSTITUTION",
            "academic_year": "2026-2027",
            "workflow_template_code": "SCRUTINY_EVC",
            "evc_required": True
        }
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]
    version = create_res.json()["version"]

    # 2. Advance to UNDER_SCRUTINY -> SCRUTINY_COMPLETED
    res_sc = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Preliminary scrutiny", "expected_version": version}
    )
    version = res_sc.json()["version"]
    res_comp = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "Preliminary scrutiny clear", "expected_version": version}
    )
    version = res_comp.json()["version"]

    # 3. Guard verification: Attempting to bypass EVC to AWAITING_COMPETENT_AUTHORITY must be blocked
    bypass_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "Attempting illegal bypass", "expected_version": version}
    )
    assert bypass_res.status_code == 400
    assert "mandatory EVC inspection" in bypass_res.json()["detail"]

    # 4. Advance legitimately to AWAITING_EVC_SCHEDULE
    res_evc_q = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_EVC_SCHEDULE", "remarks": "Routed to EVC queue", "expected_version": version}
    )
    assert res_evc_q.status_code == 200
    version = res_evc_q.json()["version"]

    # 5. Schedule EVC inspection
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    sched_res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={
            "application_id": app_id,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Prof. R. C. Verma",
            "expert_member_name": "Dr. Anjali Mehta"
        }
    )
    assert sched_res.status_code == 200
    inspection_id = sched_res.json()["id"]

    # Refresh version after automatic transition to EVC_SCHEDULED
    detail_res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    version = detail_res.json()["version"]
    assert detail_res.json()["current_stage"] == "EVC_SCHEDULED"

    # 6. Committee member submits inspection report
    report_res = client.post(
        f"/api/evc/{inspection_id}/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/evc_report_verified.pdf",
            "report_notes": "Campus facilities, labs, and faculty cadre verified as per APH norms.",
            "recommendation": "RECOMMENDED_APPROVAL"
        }
    )
    assert report_res.status_code == 200

    # Application is now EVC_COMPLETED
    detail_res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    version = detail_res.json()["version"]
    assert detail_res.json()["current_stage"] == "EVC_COMPLETED"

    # 7. Now advance to AWAITING_COMPETENT_AUTHORITY and approve
    res_ca = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "EVC recommendation positive", "expected_version": version}
    )
    assert res_ca.status_code == 200
    version = res_ca.json()["version"]

    res_appr = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Approved following satisfactory EVC inspection", "expected_version": version}
    )
    assert res_appr.status_code == 200
    assert res_appr.json()["current_stage"] == "APPROVED"


# ============================================================================
# ROUTE 3: EVC + SAC/SHC Hearing (EVC_SAC_SHC / INTAKE_VARIATION)
# ============================================================================

def test_route_3_evc_plus_sac_shc_hearing_and_deficiency_cure(client):
    """
    SIH 26262 Section A: Applications under EVC + SAC/SHC route support committee hearing,
    authorized deficiency return with mandatory justification, institution resubmission,
    and resumption of hearing review.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # 1. Create Application for EVC + SAC/SHC
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_type": "INTAKE_VARIATION",
            "academic_year": "2026-2027",
            "workflow_template_code": "EVC_SAC_SHC",
            "evc_required": True
        }
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]
    version = create_res.json()["version"]

    # 2. Advance through scrutiny to EVC queue
    res_sc = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Scrutiny", "expected_version": version}
    )
    version = res_sc.json()["version"]
    res_comp = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "Scrutiny clear", "expected_version": version}
    )
    version = res_comp.json()["version"]
    res_evc_q = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_EVC_SCHEDULE", "remarks": "EVC required", "expected_version": version}
    )
    version = res_evc_q.json()["version"]

    # 3. Schedule and complete EVC
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sched_res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={
            "application_id": app_id,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Prof. N. K. Sharma",
            "expert_member_name": "Dr. P. Sen"
        }
    )
    insp_id = sched_res.json()["id"]
    client.post(
        f"/api/evc/{insp_id}/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/evc_report_hearing.pdf",
            "report_notes": "Minor discrepancy in CAD lab seating; referred to SAC hearing.",
            "recommendation": "DEFICIENCY_NOTED"
        }
    )

    detail_res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"})
    version = detail_res.json()["version"]
    assert detail_res.json()["current_stage"] == "EVC_COMPLETED"

    # 4. Regional Officer routes to Standing Hearing Committee (SAC/CAC)
    res_sac = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_SAC_CAC_REVIEW", "remarks": "Referred to SAC Hearing Committee", "expected_version": version}
    )
    assert res_sac.status_code == 200
    version = res_sac.json()["version"]

    # 5. Standing Hearing Committee logs deficiency and returns application
    def_res = client.post(
        f"/api/applications/{app_id}/deficiencies",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "category": "INFRASTRUCTURE",
            "description": "CAD lab workstations short by 10 terminals for proposed intake.",
            "required_document": "Procurement Invoice and Installation Certificate"
        }
    )
    assert def_res.status_code == 201
    def_id = def_res.json()["id"]

    res_ret = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"to_stage": "DEFICIENCY_COMMUNICATED", "remarks": "Deficiency noted in SAC hearing; cure required within 10 days.", "expected_version": version}
    )
    assert res_ret.status_code == 200
    version = res_ret.json()["version"]
    assert res_ret.json()["current_stage"] == "DEFICIENCY_COMMUNICATED"

    # 6. Institution cures deficiency and resubmits
    cure_res = client.post(
        f"/api/applications/{app_id}/cure-deficiency/{def_id}",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "cure_remarks": "15 new high-performance CAD workstations installed and commissioned.",
            "cure_document_url": "/api/documents/download/cad_invoice.pdf"
        }
    )
    assert cure_res.status_code == 200

    res_resub = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "All CAD workstation deficiencies cured.", "expected_version": version}
    )
    assert res_resub.status_code == 200
    version = res_resub.json()["version"]

    # 7. Committee resolves deficiency and resumes hearing review
    client.post(
        f"/api/applications/{app_id}/resolve-deficiency/{def_id}",
        headers={"Authorization": f"Bearer {cm_token}"}
    )
    res_resume = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"to_stage": "AWAITING_SAC_CAC_REVIEW", "remarks": "Hearing resumed; cure verified satisfactorily.", "expected_version": version}
    )
    assert res_resume.status_code == 200
    version = res_resume.json()["version"]

    # 8. Committee recommends approval to Competent Authority
    res_ca = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "SAC recommends approval following cure verification.", "expected_version": version}
    )
    assert res_ca.status_code == 200
    version = res_ca.json()["version"]

    # 9. Competent Authority issues approval
    res_appr = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Approved on SAC recommendation.", "expected_version": version}
    )
    assert res_appr.status_code == 200
    assert res_appr.json()["current_stage"] == "APPROVED"


# ============================================================================
# ROUTE 4: Only EVC (ONLY_EVC)
# ============================================================================

def test_route_4_only_evc_direct_queue_entry(client):
    """
    SIH 26262 Section A: Applications under the 'Only EVC' route can enter the EVC
    queue directly from SUBMITTED, while non-EVC applications are blocked from doing so.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # 1. Negative test: Standard scrutiny application cannot jump SUBMITTED -> AWAITING_EVC_SCHEDULE
    std_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_type": "EOA_ANNUAL",
            "academic_year": "2026-2027",
            "workflow_template_code": "ONLY_SCRUTINY",
            "evc_required": False
        }
    ).json()

    illegal_jump = client.post(
        f"/api/applications/{std_app['id']}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_EVC_SCHEDULE", "remarks": "Attempting illegal direct jump"}
    )
    assert illegal_jump.status_code == 400
    assert "Direct transition from 'SUBMITTED' to 'AWAITING_EVC_SCHEDULE' is only permitted" in illegal_jump.json()["detail"]

    # 2. Positive test: ONLY_EVC application moves directly from SUBMITTED -> AWAITING_EVC_SCHEDULE
    evc_only_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_type": "CLOSURE_PROGRAM",
            "academic_year": "2026-2027",
            "workflow_template_code": "ONLY_EVC",
            "evc_required": True
        }
    ).json()
    app_id = evc_only_app["id"]
    version = evc_only_app["version"]

    direct_evc_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_EVC_SCHEDULE", "remarks": "Direct routing to EVC queue for infrastructure verification", "expected_version": version}
    )
    assert direct_evc_res.status_code == 200
    assert direct_evc_res.json()["current_stage"] == "AWAITING_EVC_SCHEDULE"
    assert direct_evc_res.json()["evc_required"] is True
    version = direct_evc_res.json()["version"]

    # 3. Schedule, conduct inspection, and complete
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    sched_res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {evc_token}"},
        json={
            "application_id": app_id,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Prof. B. D. Joshi",
            "expert_member_name": "Dr. Maya Swaminathan"
        }
    )
    insp_id = sched_res.json()["id"]

    client.post(
        f"/api/evc/{insp_id}/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/closure_inspection.pdf",
            "report_notes": "Infrastructure verification complete and approved.",
            "recommendation": "RECOMMENDED_APPROVAL"
        }
    )

    detail = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_token}"}).json()
    version = detail["version"]
    assert detail["current_stage"] == "EVC_COMPLETED"

    # 4. Advance to AWAITING_COMPETENT_AUTHORITY -> APPROVED
    res_ca = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "AWAITING_COMPETENT_AUTHORITY", "remarks": "Ready for final order", "expected_version": version}
    )
    version = res_ca.json()["version"]

    res_appr = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "APPROVED", "remarks": "Approved on EVC recommendation.", "expected_version": version}
    )
    assert res_appr.status_code == 200
    assert res_appr.json()["current_stage"] == "APPROVED"


# ============================================================================
# STATUTORY SAFEGUARD & ROLE AUTHORIZATION GUARDS
# ============================================================================

def test_statutory_safeguard_approval_reserved_for_competent_authority(client):
    """
    SIH 26262 Regulatory Safeguard: Automation supports the process but does not
    replace decisions reserved for the Competent Authority. Regional Officers,
    Bureau Officers, and Institution users cannot grant approvals or overrides.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    # Application 6 in seed data is at AWAITING_COMPETENT_AUTHORITY
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.current_stage == "AWAITING_COMPETENT_AUTHORITY").first()
        assert app is not None
        app_id = app.id
    finally:
        db.close()

    # 1. Regional officer attempts to approve -> 403 Forbidden
    ro_attempt = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "APPROVED", "remarks": "Unauthorized approval attempt"}
    )
    assert ro_attempt.status_code == 403
    assert "not permitted to advance application" in ro_attempt.json()["detail"]

    # 2. Institution admin attempts to approve -> 403 Forbidden
    inst_attempt = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "APPROVED", "remarks": "Unauthorized self-approval"}
    )
    assert inst_attempt.status_code == 403

    # 3. Mandatory justification on rejection
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    no_reason = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"to_stage": "REJECTED", "remarks": ""}
    )
    assert no_reason.status_code == 400
    assert "recorded reason/justification is mandatory" in no_reason.json()["detail"]

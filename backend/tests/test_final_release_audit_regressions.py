import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.institution import Institution
from app.models.application import Application, Deficiency
from app.models.compliance import ComplianceUndertaking
from app.models.evc import EVCInspection
from app.models.alert import AlertEscalation
from app.services.compliance_service import ComplianceService
from app.services.document_intelligence_service import DocumentIntelligenceService

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_evc_report_virtual_meeting_url_persists_without_recording(client):
    """
    Regression Test for Defect 1:
    EVC report submitted with virtual_meeting_url but without virtual_recording_url
    must commit and persist meeting URL correctly.
    """
    evc_coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    db: Session = SessionLocal()
    try:
        # Create an inspection scheduled for virtual meeting
        insp = EVCInspection(
            application_id=1,
            inspection_type="HYBRID_VIRTUAL",
            status="SCHEDULED",
            scheduled_date=datetime.now(timezone.utc) + timedelta(days=2),
            convener_name="Prof. Test Convener",
            expert_member_name="Dr. Test Expert"
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)
        insp_id = insp.id
    finally:
        db.close()

    report_payload = {
        "report_url": "/api/documents/download/virtual_report.pdf",
        "report_notes": "Virtual scrutiny of lab facilities conducted via video link.",
        "recommendation": "RECOMMENDED_APPROVAL",
        "virtual_meeting_url": "https://teams.microsoft.com/l/meetup-join/aicte-evc-101"
        # virtual_recording_url omitted intentionally
    }

    res = client.post(
        f"/api/evc/{insp_id}/submit-report",
        headers={"Authorization": f"Bearer {evc_coord_token}"},
        json=report_payload
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] in ["REPORT_SUBMITTED", "RECOMMENDED_APPROVAL"]

    # Verify directly in DB that virtual_meeting_url was committed
    db_verify = SessionLocal()
    try:
        updated = db_verify.query(EVCInspection).filter(EVCInspection.id == insp_id).first()
        assert updated is not None
        assert updated.virtual_meeting_url == "https://teams.microsoft.com/l/meetup-join/aicte-evc-101"
    finally:
        db_verify.close()


def test_document_intelligence_leap_year_feb_29():
    """
    Regression Test for Defect 2:
    Lease start date on Feb 29 (leap year) + duration must safely resolve to Feb 28
    in non-leap years without raising ValueError.
    """
    # 2024 is a leap year (Feb 29 exists); 2054 (30 yrs later) is not a leap year
    txt = "Lease deed registered. Valid for a period of 30 years commencing from 29/02/2024 by order."
    pages_text = {1: txt}
    candidates = DocumentIntelligenceService.extract_candidate_fields(pages_text=pages_text, full_text=txt)
    assert "expiry_date" in candidates
    # Expiry is 30 years later minus 1 day, safely bounded to Feb 27, 2054
    assert candidates["expiry_date"]["value"] == "2054-02-27"


def test_compliance_effective_status_date_object():
    """
    Regression Test for Defect 3:
    ComplianceService.get_effective_status must safely handle due_date as date
    object without raising AttributeError for tzinfo or TypeError for subtraction.
    """
    db: Session = SessionLocal()
    try:
        inst = db.query(Institution).first()
        # Test overdue date object
        past_date = date.today() - timedelta(days=5)
        undertaking_past = ComplianceUndertaking(
            institution_id=inst.id,
            category="INFRASTRUCTURE",
            title="Barrier Free Ramp Undertaking",
            status="NOT_YET_DUE",
            due_date=past_date
        )
        status_past = ComplianceService.get_effective_status(undertaking_past)
        assert status_past == "OVERDUE"

        # Test due soon date object (within 14 days)
        soon_date = date.today() + timedelta(days=7)
        undertaking_soon = ComplianceUndertaking(
            institution_id=inst.id,
            category="SAFETY",
            title="Anti-ragging Undertaking",
            status="NOT_YET_DUE",
            due_date=soon_date
        )
        status_soon = ComplianceService.get_effective_status(undertaking_soon)
        assert status_soon == "DUE_SOON"

        # Test far future date object
        far_date = date.today() + timedelta(days=60)
        undertaking_far = ComplianceUndertaking(
            institution_id=inst.id,
            category="FACULTY",
            title="Faculty Cadre Ratio",
            status="NOT_YET_DUE",
            due_date=far_date
        )
        status_far = ComplianceService.get_effective_status(undertaking_far)
        assert status_far == "NOT_YET_DUE"
    finally:
        db.close()


def test_escalation_acknowledgement_fail_closed_unassigned_regional_officer(client):
    """
    Regression Test for Defect 4:
    Regional Officer without an assigned region must FAIL CLOSED (403 Forbidden)
    when attempting to acknowledge an alert escalation.
    """
    db: Session = SessionLocal()
    try:
        # Create unassigned regional officer user
        user = db.query(User).filter(User.email == "ro.western@aicte.gov.in").first()
        token = get_auth_token(client, "ro.western@aicte.gov.in")

        # Temporarily clear region to simulate unassigned officer
        original_region = user.region
        user.region = None
        db.commit()

        # Find or create an escalation
        esc = db.query(AlertEscalation).first()
        if not esc:
            esc = AlertEscalation(
                entity_type="APPLICATION",
                entity_id=1,
                escalation_level="ESCALATION_L1_RO",
                recipient_role="REGIONAL_OFFICER",
                status="TRIGGERED"
            )
            db.add(esc)
            db.commit()
            db.refresh(esc)
        esc_id = esc.id
    finally:
        db.close()

    try:
        ack_res = client.post(
            f"/api/alerts/escalations/{esc_id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
            json={"resolution_notes": "Attempting ack without assigned region"}
        )
        assert ack_res.status_code == 403
        assert "no assigned regional jurisdiction" in ack_res.json()["detail"].lower()
    finally:
        # Restore region
        db_restore = SessionLocal()
        try:
            u = db_restore.query(User).filter(User.email == "ro.western@aicte.gov.in").first()
            u.region = original_region
            db_restore.commit()
        finally:
            db_restore.close()


def test_committee_member_idor_blocked_on_unassigned_application(client):
    """
    Regression Test for Defect 5:
    Committee Member cannot view application detail or case brief for applications
    in pre-committee stages (e.g. UNDER_SCRUTINY) when not assigned to EVC.
    """
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    # Create new application at SUBMITTED / UNDER_SCRUTINY stage
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["id"]

    # Committee member accesses application detail -> Must be 403 Forbidden
    detail_res = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {cm_token}"}
    )
    assert detail_res.status_code == 403

    # Committee member accesses case brief -> Must be 403 Forbidden
    brief_res = client.get(
        f"/api/applications/{app_id}/case-brief",
        headers={"Authorization": f"Bearer {cm_token}"}
    )
    assert brief_res.status_code == 403


def test_evc_coordinator_idor_blocked_on_non_evc_application(client):
    """
    Regression Test for Defect 5 (EVC Coordinator):
    EVC Coordinator cannot access application details for applications outside
    EVC purview (e.g. EOA_ANNUAL with evc_required=False and workflow ONLY_SCRUTINY).
    """
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

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
    app_id = create_res.json()["id"]

    # EVC coordinator attempts access -> Must be 403 Forbidden
    res = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {evc_token}"}
    )
    assert res.status_code == 403
    assert "EVC inspection scope" in res.json()["detail"]


def test_create_application_sequential_collision_avoidance(client):
    """
    Regression Test for Defect 6:
    Application creation must detect and skip pre-existing application numbers
    rather than failing on database unique constraint collision.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    db: Session = SessionLocal()
    try:
        count = db.query(Application).count() + 101
        conflicting_num = f"AICTE-2026-EOA-{count:05d}"
        inst = db.query(Institution).first()
        pre_existing = Application(
            application_number=conflicting_num,
            institution_id=inst.id,
            academic_year="2026-2027",
            application_type="EOA_ANNUAL",
            workflow_template_code="ONLY_SCRUTINY",
            current_stage="SUBMITTED"
        )
        db.add(pre_existing)
        db.commit()
    finally:
        db.close()

    # Create application via API -> should increment count to avoid conflict
    res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_type": "EOA_ANNUAL", "academic_year": "2026-2027"}
    )
    assert res.status_code == 201
    created_num = res.json()["application_number"]
    assert created_num != conflicting_num
    assert created_num.startswith("AICTE-2026-EOA-")


def test_deficiency_resubmission_blocked_when_open_or_blank_cure(client):
    """
    Regression Test for Defect 7:
    Resubmission must be blocked if any deficiency remains OPEN or has empty/blank cure remarks.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    db: Session = SessionLocal()
    try:
        inst = db.query(Institution).first()
        app_obj = Application(
            application_number=f"AICTE-2026-TEST-{int(datetime.now().timestamp())}",
            institution_id=inst.id,
            academic_year="2026-2027",
            application_type="EOA_ANNUAL",
            workflow_template_code="ONLY_SCRUTINY",
            current_stage="DEFICIENCY_COMMUNICATED",
            version=1
        )
        db.add(app_obj)
        db.flush()

        def_item = Deficiency(
            application_id=app_obj.id,
            category="INFRASTRUCTURE",
            description="Barrier-free ramp missing",
            status="OPEN",
            cure_remarks="   "  # whitespace-only cure remarks
        )
        db.add(def_item)
        db.commit()
        app_id = app_obj.id
    finally:
        db.close()

    # Attempt transition to RESUBMITTED
    res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "Resubmitting with blank cure"}
    )
    assert res.status_code == 400
    assert "deficiency items do not have required cure" in res.json()["detail"]

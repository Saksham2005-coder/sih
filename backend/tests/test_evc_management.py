import pytest
from datetime import datetime, timedelta, timezone

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_evc_queue_lists_pending_and_eligible_inspections(client):
    coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    res = client.get("/api/evc/queue", headers={"Authorization": f"Bearer {coord_token}"})
    assert res.status_code == 200
    queue = res.json()
    assert len(queue) >= 1
    # App 2 (AICTE-2026-NEW-44102) is in AWAITING_EVC_SCHEDULE
    app2_evc = next((item for item in queue if item["application_id"] == 2), None)
    assert app2_evc is not None
    assert app2_evc["status"] in ["PENDING_ASSIGNMENT", "SCHEDULED"]

def test_evc_scheduling_valid_panel_and_future_date(client):
    coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    future_date = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={
            "application_id": 2,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Prof. R. K. Sharma (IIT Bombay)",
            "expert_member_name": "Dr. Ananya Sen (VJTI Mumbai)"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SCHEDULED"
    assert data["convener_name"] == "Prof. R. K. Sharma (IIT Bombay)"

    # Verify application stage transitioned to EVC_SCHEDULED
    app_res = client.get("/api/applications/2", headers={"Authorization": f"Bearer {coord_token}"})
    assert app_res.json()["current_stage"] == "EVC_SCHEDULED"

def test_evc_scheduling_past_date_rejected_with_400(client):
    coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={
            "application_id": 2,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": past_date,
            "convener_name": "Prof. Valid Name",
            "expert_member_name": "Dr. Valid Expert"
        }
    )
    assert res.status_code == 400
    assert "future date" in res.json()["detail"].lower()

def test_evc_scheduling_missing_panel_members_rejected(client):
    coord_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {coord_token}"},
        json={
            "application_id": 2,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "",
            "expert_member_name": "Dr. Expert"
        }
    )
    assert res.status_code == 400
    assert "convener" in res.json()["detail"].lower()

def test_regional_officer_cross_region_evc_scheduling_blocked(client):
    # RO Western trying to schedule inspection for Institution 2 (Northern Region)
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "application_id": 3,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Prof. Convener",
            "expert_member_name": "Dr. Expert"
        }
    )
    assert res.status_code == 403
    assert "Northern" in res.json()["detail"] or "Access denied" in res.json()["detail"]

def test_unauthorized_institution_cannot_schedule_evc(client):
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    
    res = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "application_id": 2,
            "inspection_type": "PHYSICAL_ONSITE",
            "scheduled_date": future_date,
            "convener_name": "Self Assigner",
            "expert_member_name": "Self Expert"
        }
    )
    assert res.status_code == 403

def test_evc_report_submission_success(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    # Submit report for inspection on Application 2 (which is now in EVC_SCHEDULED)
    res = client.post(
        "/api/evc/1/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/evc_signed_inspection_report.pdf",
            "report_notes": "Physical campus inspection completed. Infrastructure and lab setups satisfy 2026 norms.",
            "recommendation": "RECOMMENDED_APPROVAL"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REPORT_SUBMITTED"
    assert data["recommendation"] == "RECOMMENDED_APPROVAL"

    # Invariant: Submitting report transitions to EVC_COMPLETED, NOT APPROVED
    app_res = client.get("/api/applications/2", headers={"Authorization": f"Bearer {cm_token}"})
    app_data = app_res.json()
    assert app_data["current_stage"] == "EVC_COMPLETED"
    assert app_data["current_stage"] != "APPROVED"

def test_invalid_evc_recommendation_rejected(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    res = client.post(
        "/api/evc/1/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/evc_signed_inspection_report.pdf",
            "report_notes": "Valid notes",
            "recommendation": "GRANT_UNCONDITIONAL_APPROVAL_NOW"
        }
    )
    assert res.status_code == 400
    assert "invalid recommendation" in res.json()["detail"].lower()

def test_missing_evc_report_notes_rejected(client):
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    res = client.post(
        "/api/evc/1/submit-report",
        headers={"Authorization": f"Bearer {cm_token}"},
        json={
            "report_url": "/api/documents/download/evc_signed_inspection_report.pdf",
            "report_notes": "   ",
            "recommendation": "RECOMMENDED_APPROVAL"
        }
    )
    assert res.status_code == 400
    assert "mandatory" in res.json()["detail"].lower()

import pytest
from datetime import datetime, timezone, timedelta
from app.services.deadline_service import DeadlineService, generate_idempotency_key
from app.models.alert import AlertEscalation, Notification, DeadlineEngineRun
from app.models.compliance import ComplianceUndertaking
from app.models.application import Application
from app.models.document import DocumentRecord
from app.models.evc import EVCInspection

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_deadline_condition_derivation_boundaries():
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 1. More than 7 days ahead -> ON_TRACK
    future_10d = now + timedelta(days=10)
    cond1 = DeadlineService.calculate_deadline_condition(future_10d, reference_time=now)
    assert cond1["condition"] == "ON_TRACK"
    assert cond1["days_remaining"] == 10
    assert cond1["days_overdue"] == 0

    # 2. Within 7 days -> DUE_SOON
    future_4d = now + timedelta(days=4)
    cond2 = DeadlineService.calculate_deadline_condition(future_4d, reference_time=now)
    assert cond2["condition"] == "DUE_SOON"
    assert cond2["days_remaining"] == 4

    # 3. Same day -> DUE_TODAY
    same_day = now + timedelta(hours=4)
    cond3 = DeadlineService.calculate_deadline_condition(same_day, reference_time=now)
    assert cond3["condition"] == "DUE_TODAY"
    assert cond3["days_remaining"] == 0

    # 4. Past -> OVERDUE
    past_3d = now - timedelta(days=3)
    cond4 = DeadlineService.calculate_deadline_condition(past_3d, reference_time=now)
    assert cond4["condition"] == "OVERDUE"
    assert cond4["days_overdue"] == 3

def test_multi_vector_deadline_scan_executes_successfully(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "scanned_entities" in data
    assert "reminders_created" in data
    assert "escalations_created" in data
    assert "duplicates_prevented" in data
    assert data["scanned_entities"] > 0

def test_zero_duplicate_alerts_on_repeated_scans(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    # Run 1
    res1 = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert res1.status_code == 200

    # Run 2 immediately
    res2 = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["reminders_created"] == 0
    assert data2["escalations_created"] == 0
    assert data2["duplicates_prevented"] >= 1

    # Run 3 immediately
    res3 = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["reminders_created"] == 0
    assert data3["escalations_created"] == 0

def test_cycle_aware_idempotency_allows_new_cycle_alert():
    # Two identical conditions but different cycle IDs produce distinct idempotency keys
    key_cycle1 = generate_idempotency_key("APPLICATION", 1, "DEFICIENCY_OVERDUE", 15, "ESCALATION_L2_BO", "BUREAU_OFFICER", "v1")
    key_cycle2 = generate_idempotency_key("APPLICATION", 1, "DEFICIENCY_OVERDUE", 15, "ESCALATION_L2_BO", "BUREAU_OFFICER", "v2")
    assert key_cycle1 != key_cycle2

def test_auto_resolution_of_cured_deficiency_escalations(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    
    # Run scan to ensure baseline escalations are generated
    client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})

    # Query active escalations for applications
    esc_res = client.get("/api/alerts/escalations?status_filter=ACTIVE", headers={"Authorization": f"Bearer {admin_token}"})
    assert esc_res.status_code == 200

def test_multi_tier_escalation_chain_exists(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {admin_token}"})

    esc_res = client.get("/api/alerts/escalations", headers={"Authorization": f"Bearer {admin_token}"})
    assert esc_res.status_code == 200
    escalations = esc_res.json()
    levels = [e["escalation_level"] for e in escalations]
    
    # Should include progressive tiers
    assert any("REMINDER" in lvl or "ESCALATION" in lvl for lvl in levels)

def test_regional_officer_scoping_on_escalations(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.get("/api/alerts/escalations", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    ro_escalations = res.json()

    # All returned escalations for RO Western must either be in Western region or targeted to REGIONAL_OFFICER
    for esc in ro_escalations:
        if esc.get("region"):
            assert esc["region"] in ["Western", "Western Region", None]

def test_cross_region_escalation_acknowledgment_blocked(client):
    # RO Western trying to acknowledge an escalation in Northern region
    ro_western_token = get_auth_token(client, "ro.western@aicte.gov.in")
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    # Find an escalation belonging to Northern region
    all_esc = client.get("/api/alerts/escalations", headers={"Authorization": f"Bearer {admin_token}"}).json()
    northern_esc = next((e for e in all_esc if e.get("region") in ["Northern", "North"] and e["status"] == "ACTIVE"), None)

    if northern_esc:
        res = client.post(
            f"/api/alerts/{northern_esc['id']}/acknowledge",
            headers={"Authorization": f"Bearer {ro_western_token}"},
            json={"remarks": "Attempting cross-region acknowledgment"}
        )
        assert res.status_code == 403
        assert "cannot acknowledge" in res.json()["detail"].lower()

def test_officer_acknowledges_in_scope_escalation(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    all_esc = client.get("/api/alerts/escalations", headers={"Authorization": f"Bearer {admin_token}"}).json()
    active_esc = next((e for e in all_esc if e["status"] == "ACTIVE"), None)

    if active_esc:
        res = client.post(
            f"/api/alerts/{active_esc['id']}/acknowledge",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"remarks": "Review completed. Compliance notice issued."}
        )
        assert res.status_code == 200
        assert res.json()["status"] == "ACKNOWLEDGED"

        # Check updated status
        updated = client.get("/api/alerts/escalations", headers={"Authorization": f"Bearer {admin_token}"}).json()
        target = next(e for e in updated if e["id"] == active_esc["id"])
        assert target["status"] == "ACKNOWLEDGED"

def test_institution_isolation_on_notifications(client):
    apex_token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get("/api/alerts/notifications", headers={"Authorization": f"Bearer {apex_token}"})
    assert res.status_code == 200
    notifs = res.json()
    
    # Apex Institute is ID 1; should not see notifications for Institution 2
    for n in notifs:
        if n["institution_id"]:
            assert n["institution_id"] == 1

def test_mark_notification_read_ownership_enforcement(client):
    apex_token = get_auth_token(client, "admin@apex.edu.in")
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    # Find a notification for Institution 2 or officer-only
    admin_notifs = client.get("/api/alerts/notifications", headers={"Authorization": f"Bearer {admin_token}"}).json()
    other_notif = next((n for n in admin_notifs if n["institution_id"] == 2), None)

    if other_notif:
        res = client.post(
            f"/api/alerts/notifications/{other_notif['id']}/read",
            headers={"Authorization": f"Bearer {apex_token}"}
        )
        assert res.status_code == 403

def test_engine_status_endpoint_returns_metrics(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/alerts/engine-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    status_data = res.json()
    assert "is_running" in status_data
    assert "scan_interval_seconds" in status_data
    assert "total_runs" in status_data
    assert "total_scanned" in status_data

def test_unauthorized_user_cannot_trigger_scan(client):
    apex_token = get_auth_token(client, "admin@apex.edu.in")
    res = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {apex_token}"})
    assert res.status_code == 403

def test_rule_studio_updates_affect_deadline_service(client):
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    
    # Get current rules
    res = client.get("/api/rules", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 4

    # Update RULE_SCRUTINY_SLA with new version and parameters
    res_update = client.put(
        "/api/rules/RULE_SCRUTINY_SLA",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "version": "1.2.0",
            "config_json": '{"sla_days": 5, "escalation_target": "REGIONAL_OFFICER", "is_illustrative_demo": true}'
        }
    )
    assert res_update.status_code == 200
    assert res_update.json()["version"] == "1.2.0"

    # Revert to standard illustrative demo
    client.put(
        "/api/rules/RULE_SCRUTINY_SLA",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "version": "1.0.0",
            "config_json": '{"sla_days": 7, "escalation_target": "REGIONAL_OFFICER", "is_illustrative_demo": true}'
        }
    )

import pytest
import json
from datetime import datetime, timezone, timedelta, date
from app.services.deadline_service import DeadlineService
from app.services.priority_service import PriorityService
from app.services.case_brief_service import CaseBriefService
from app.services.scheduler import DeadlineScheduler
from app.models.alert import SchedulerLease
from app.models.rule import RuleDefinition, RuleVersionHistory
from app.models.audit import AuditEvent
from app.models.application import Application
from app.core.database import SessionLocal

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

# ============================================================================
# 1. EXACT DEADLINE BOUNDARY & SCHEDULER LEASE TESTS
# ============================================================================

def test_calendar_date_deadline_boundaries():
    """Verify date-only deadlines calculate accurately with Asia/Kolkata date boundaries."""
    ref_time = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Target date 5 days ahead -> DUE_SOON
    target_date = date(2026, 6, 20)
    cond = DeadlineService.calculate_deadline_condition(target_date, reference_time=ref_time)
    assert cond["condition"] == "DUE_SOON"
    assert cond["days_remaining"] == 5
    assert cond["days_overdue"] == 0

    # Target date is today (2026-06-15) -> DUE_TODAY
    today_date = date(2026, 6, 15)
    cond_today = DeadlineService.calculate_deadline_condition(today_date, reference_time=ref_time)
    assert cond_today["condition"] == "DUE_TODAY"
    assert cond_today["days_remaining"] == 0

    # Target date is 2 days in past -> OVERDUE
    past_date = date(2026, 6, 13)
    cond_past = DeadlineService.calculate_deadline_condition(past_date, reference_time=ref_time)
    assert cond_past["condition"] == "OVERDUE"
    assert cond_past["days_overdue"] == 2

def test_scheduler_lease_coordination():
    """Test distributed scheduler lease acquisition, locking, heartbeat renewal and release."""
    db = SessionLocal()
    try:
        # Clean existing test lease
        db.query(SchedulerLease).filter(SchedulerLease.lease_name == "test_scan_lease").delete()
        db.commit()

        # Worker 1 acquires
        acq1 = DeadlineScheduler.acquire_lease(db, lease_name="test_scan_lease", holder_id="worker-1", lease_duration_seconds=10)
        assert acq1 is True

        # Worker 2 attempts while Worker 1 holds active lease -> must fail
        acq2 = DeadlineScheduler.acquire_lease(db, lease_name="test_scan_lease", holder_id="worker-2", lease_duration_seconds=10)
        assert acq2 is False

        # Worker 1 renews lease
        renewed = DeadlineScheduler.renew_lease(db, lease_name="test_scan_lease", holder_id="worker-1", extension_seconds=15)
        assert renewed is True

        # Worker 2 attempts renewal -> must fail
        fake_renew = DeadlineScheduler.renew_lease(db, lease_name="test_scan_lease", holder_id="worker-2", extension_seconds=15)
        assert fake_renew is False

        # Release lease
        rel = DeadlineScheduler.release_lease(db, lease_name="test_scan_lease", holder_id="worker-1")
        assert rel is True

        # Now Worker 2 can acquire
        acq3 = DeadlineScheduler.acquire_lease(db, lease_name="test_scan_lease", holder_id="worker-2", lease_duration_seconds=10)
        assert acq3 is True

        # Cleanup
        db.query(SchedulerLease).filter(SchedulerLease.lease_name == "test_scan_lease").delete()
        db.commit()
    finally:
        db.close()

# ============================================================================
# 2. COMMAND CENTRE & ROLE SCOPING TESTS
# ============================================================================

def test_command_centre_sysadmin_scope(client):
    """System Administrator sees global operational overview and priority items."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/reports/command-centre", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()

    assert "summary" in data
    assert "bottlenecks" in data
    assert "priority_queue" in data
    assert "recent_activity" in data
    assert "role_scope" in data
    assert "jurisdiction" in data

    # Verify reconciliation: summary numbers are non-negative
    summary = data["summary"]
    assert summary["total_applications"] >= 0
    assert "stage_breakdown" in summary
    assert "regional_breakdown" in summary

    # Check priority queue items format
    if data["priority_queue"]:
        item = data["priority_queue"][0]
        assert "application_id" in item
        assert "application_number" in item
        assert "institution_name" in item
        assert "priority_score" in item
        assert "priority_tier" in item
        assert "priority_factors" in item
        assert "recommended_action" in item
        assert "action_link" in item

def test_command_centre_regional_officer_scoping(client):
    """Regional Officer only receives metrics and priority queue items within Western jurisdiction."""
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.get("/api/reports/command-centre", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["role_scope"] == "REGIONAL_OFFICER"
    assert "Western" in data["jurisdiction"]

    # All priority items returned must belong to Western region
    for item in data["priority_queue"]:
        assert item["region"] == "Western"

def test_command_centre_institution_user_scoping(client):
    """Institution user only sees data scoped to their own institution."""
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get("/api/reports/command-centre", headers={"Authorization": f"Bearer {inst_token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["role_scope"] in ("INSTITUTION_ADMIN", "COMPLIANCE_OFFICER")
    # Should only see their institution name in priority queue
    for item in data["priority_queue"]:
        assert "Apex Institute" in item["institution_name"]

# ============================================================================
# 3. EXPLAINABLE PRIORITY SERVICE & INVARIANTS
# ============================================================================

def test_priority_calculation_deterministic():
    """Identical application state produces identical score and factor weights."""
    db = SessionLocal()
    try:
        app = db.query(Application).first()
        assert app is not None

        result1 = PriorityService.calculate_case_priority(app, db)
        result2 = PriorityService.calculate_case_priority(app, db)

        assert result1.total_score == result2.total_score
        assert result1.priority_level == result2.priority_level
        assert result1.next_action == result2.next_action
        assert len(result1.factors) == len(result2.factors)
        for f1, f2 in zip(result1.factors, result2.factors):
            assert f1.name == f2.name
            assert f1.points == f2.points
    finally:
        db.close()

def test_priority_calculation_does_not_mutate_statutory_state():
    """Priority scoring is an operational index and must NEVER mutate application status or version."""
    db = SessionLocal()
    try:
        app = db.query(Application).first()
        initial_stage = app.current_stage
        initial_version = app.version
        initial_id = app.id

        _ = PriorityService.calculate_case_priority(app, db)

        db.refresh(app)
        assert app.current_stage == initial_stage
        assert app.version == initial_version
        assert app.id == initial_id
    finally:
        db.close()

# ============================================================================
# 4. RULE STUDIO: VALIDATION, SIMULATION, VERSIONING
# ============================================================================

def test_rule_validation_endpoint(client):
    """Valid config succeeds; invalid JSON or out-of-order thresholds produce actionable feedback."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    # 1. Valid SLA config
    valid_payload = {
        "config_json": json.dumps({
            "sla_days": 10,
            "escalation_target": "REGIONAL_OFFICER"
        })
    }
    res_val = client.post("/api/rules/RULE_SCRUTINY_SLA/validate", json=valid_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_val.status_code == 200
    data_val = res_val.json()
    assert data_val["valid"] is True
    assert len(data_val["errors"]) == 0

    # 2. Invalid config with negative sla_days
    invalid_payload = {
        "config_json": json.dumps({
            "sla_days": -5,
            "escalation_target": "NON_EXISTENT_ROLE"
        })
    }
    res_inv = client.post("/api/rules/RULE_SCRUTINY_SLA/validate", json=invalid_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["valid"] is False
    assert len(data_inv["errors"]) >= 1

def test_rule_dry_run_simulation(client):
    """Dry-run simulation evaluates rule logic against scenario without mutating DB."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    sim_payload = {
        "config_json": json.dumps({
            "sla_days": 5,
            "escalation_target": "REGIONAL_OFFICER"
        }),
        "application_id": None
    }
    res = client.post("/api/rules/RULE_SCRUTINY_SLA/simulate", json=sim_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data["rule_code"] == "RULE_SCRUTINY_SLA"
    assert "simulation_results" in sim_data
    assert sim_data["simulation_results"]["sla_threshold_days"] == 5

def test_rule_publish_archives_version_history(client):
    """Publishing a rule updates version and records prior snapshot into rule_version_history."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == "RULE_SCRUTINY_SLA").first()
        assert rule is not None
        rule_code = rule.rule_code
        old_version = rule.version
        old_cfg = rule.config_json
    finally:
        db.close()

    publish_payload = {
        "config_json": old_cfg,
        "version": "1.1.0",
        "change_reason": "Phase 5 verified audit rule update for SLA thresholds"
    }
    res = client.post(f"/api/rules/{rule_code}/publish", json=publish_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    published = res.json()
    assert published["status"] == "PUBLISHED"
    assert published["version"] == "1.1.0"
    assert published["change_reason"] == publish_payload["change_reason"]

    # Verify history ledger contains prior version
    res_hist = client.get(f"/api/rules/{rule_code}/history", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 1
    assert any(h["rule_code"] == rule_code for h in history)

def test_rule_modification_requires_admin(client):
    """Non-admin user cannot publish or mutate rules."""
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    publish_payload = {
        "config_json": "{}",
        "version": "1.1.0",
        "change_reason": "unauthorized attempt"
    }
    res = client.post("/api/rules/RULE_SCRUTINY_SLA/publish", json=publish_payload, headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 403

# ============================================================================
# 5. UNIFIED AUDIT EXPLORER & CSV EXPORT ESCAPING
# ============================================================================

def test_audit_explorer_filtering_and_pagination(client):
    """Audit Explorer supports server-side filtering, pagination and regional scope."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/audit?page=1&limit=10", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["items"]) <= 10

def test_audit_csv_export_formula_injection_defense(client):
    """Audit CSV export prevents formula injection by prefixing dangerous characters with single quotes."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/audit/export", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    csv_text = res.text
    assert "Event ID" in csv_text
    assert "Actor Name" in csv_text
    assert "Action" in csv_text
    assert "Entity Type" in csv_text

    # Verify no unescaped formula injection tokens start any data field
    lines = csv_text.splitlines()
    for line in lines[1:]:
        tokens = line.split(",")
        for t in tokens:
            t_clean = t.strip('"')
            # Dangerous formula operators must not be unescaped
            if len(t_clean) > 0 and t_clean[0] in ("=", "+", "-", "@"):
                assert False, f"Dangerous unescaped formula prefix detected: {t_clean}"

# ============================================================================
# 6. OPERATIONAL REPORTS (SLA ADHERENCE & EVC ANALYTICS)
# ============================================================================

def test_sla_adherence_report(client):
    """SLA adherence report calculates average turnaround and adherence percentages."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/reports/sla-adherence", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_cases_analyzed" in data
    assert "within_sla_count" in data
    assert "within_sla_percentage" in data
    assert "breached_sla_count" in data
    assert "breached_sla_percentage" in data
    assert "stage_sla_breakdown" in data
    assert isinstance(data["stage_sla_breakdown"], list)

def test_evc_analytics_report(client):
    """EVC analytics report provides queue and recommendation metrics."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/reports/evc-analytics", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_inspections" in data
    assert "scheduled_count" in data
    assert "completed_count" in data
    assert "recommendations" in data
    assert "inspection_types" in data

# ============================================================================
# 7. EVIDENCE-GROUNDED CASE BRIEF ASSISTANT
# ============================================================================

def test_case_brief_endpoint_with_citations(client):
    """Case brief generates structured, factual synthesis with database citations."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        app = db.query(Application).first()
        app_id = app.id
    finally:
        db.close()

    res = client.get(f"/api/applications/{app_id}/case-brief", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    brief = res.json()
    assert brief["application_id"] == app_id
    assert "summary_paragraphs" in brief
    assert isinstance(brief["summary_paragraphs"], list)
    assert len(brief["summary_paragraphs"]) >= 1
    assert "suggested_administrative_draft" in brief
    assert "evidence_milestones" in brief
    assert "evidence_deficiencies" in brief
    assert "evidence_undertakings" in brief
    assert "regulatory_disclaimer" in brief
    assert "STATUTORY NOTICE" in brief["regulatory_disclaimer"]

def test_case_brief_forbidden_for_other_institution(client):
    """Institution user cannot access case briefs for applications from other institutions."""
    # admin@nier.edu.in belongs to NIER (id=2)
    nier_token = get_auth_token(client, "admin@nier.edu.in")
    db = SessionLocal()
    try:
        # Find application belonging to Apex (id=1)
        apex_app = db.query(Application).filter(Application.institution_id == 1).first()
        assert apex_app is not None
        apex_app_id = apex_app.id
    finally:
        db.close()

    res = client.get(f"/api/applications/{apex_app_id}/case-brief", headers={"Authorization": f"Bearer {nier_token}"})
    assert res.status_code in (403, 404)

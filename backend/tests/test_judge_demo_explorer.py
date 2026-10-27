import pytest
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.application import Application, Deficiency
from app.models.audit import AuditEvent

def get_auth_token(client, email="sysadmin@aicte.gov.in", password="Password123!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]

def test_demo_scenarios_returns_five_curated_routes(client):
    """Verifies that /api/demo/scenarios returns all 5 authentic synthetic scenarios for authenticated users."""
    token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/demo/scenarios", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 5

    # Check Scenario 1: New Institution with Mandatory EVC
    s1 = next(s for s in scenarios if s["scenario_id"] == "scenario-1-new-inst-evc")
    assert s1["scenario_number"] == 1
    assert "EVC" in s1["title"]
    assert s1["application_number"] == "AICTE-2026-NEW-44102"
    assert s1["recommended_persona"]["role"] == "EVC_COORDINATOR"

    # Check Scenario 2: EOA Scrutiny-Only Track
    s2 = next(s for s in scenarios if s["scenario_id"] == "scenario-2-eoa-scrutiny-only")
    assert s2["scenario_number"] == 2
    assert s2["route_code"] == "ONLY_SCRUTINY"
    assert s2["application_number"] == "AICTE-2026-EOA-55910"
    assert s2["recommended_persona"]["role"] == "REGIONAL_OFFICER"

    # Check Scenario 3: Deficiency Cure Loop
    s3 = next(s for s in scenarios if s["scenario_id"] == "scenario-3-deficiency-cure-loop")
    assert s3["scenario_number"] == 3
    assert s3["application_number"] == "AICTE-2026-EOA-98124"
    assert s3["recommended_persona"]["role"] == "INSTITUTION_ADMIN"

    # Check Scenario 4: Continuous Compliance & Escalation
    s4 = next(s for s in scenarios if s["scenario_id"] == "scenario-4-expiry-escalation")
    assert s4["scenario_number"] == 4
    assert s4["recommended_persona"]["role"] == "COMPLIANCE_OFFICER"

    # Check Scenario 5: Competent Authority Decision
    s5 = next(s for s in scenarios if s["scenario_id"] == "scenario-5-evc-ca-decision")
    assert s5["scenario_number"] == 5
    assert s5["recommended_persona"]["role"] == "COMPETENT_AUTHORITY"
    assert s5["application_number"] == "AICTE-2026-DEC-33019"

def test_demo_routes_exposes_canonical_specifications(client):
    """Verifies that /api/demo/routes returns all 4 canonical route combinations backed by the authoritative registry."""
    token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/demo/routes", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    routes = res.json()
    assert "ONLY_SCRUTINY" in routes
    assert "SCRUTINY_EVC" in routes
    assert "EVC_SAC_SHC" in routes
    assert "ONLY_EVC" in routes

    # Verify ONLY_SCRUTINY non-applicable stages have statutory rationale
    eoa_route = routes["ONLY_SCRUTINY"]
    non_app = eoa_route["non_applicable_stages"]
    evc_non_app = next(na for na in non_app if na["stage_code"] == "AWAITING_EVC_SCHEDULE")
    assert "APH" in evc_non_app["aph_rule_reference"]
    assert "Statutory Exemption" in evc_non_app["statutory_reason"]

    # Verify SCRUTINY_EVC stages include EVC
    evc_route = routes["SCRUTINY_EVC"]
    stage_codes = [s["stage_code"] for s in evc_route["stages"]]
    assert "AWAITING_EVC_SCHEDULE" in stage_codes
    assert "EVC_SCHEDULED" in stage_codes
    assert "EVC_COMPLETED" in stage_codes

    # Verify EVC_SAC_SHC route
    sac_route = routes["EVC_SAC_SHC"]
    sac_stages = [s["stage_code"] for s in sac_route["stages"]]
    assert "AWAITING_SAC_CAC_REVIEW" in sac_stages

    # Verify ONLY_EVC route
    only_evc_route = routes["ONLY_EVC"]
    only_evc_stages = [s["stage_code"] for s in only_evc_route["stages"]]
    assert "UNDER_SCRUTINY" not in only_evc_stages
    assert "EVC_SCHEDULED" in only_evc_stages

def test_explainability_telemetry_grounded_in_database(client):
    """Verifies that /api/demo/explainability returns actual database telemetry with live rule provenance."""
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        assert app is not None

        token = get_auth_token(client, "ro.western@aicte.gov.in")
        res = client.get(f"/api/demo/explainability/{app.id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()

        assert data["application"]["application_number"] == "AICTE-2026-EOA-98124"
        assert "Apex Institute of Technology" in data["application"]["institution_name"]

        # SLA tracking with verified rule provenance
        assert "days_elapsed" in data["sla_tracking"]
        assert "configured_sla_days" in data["sla_tracking"]
        assert data["sla_tracking"]["sla_status"] in ["ON_TRACK", "APPROACHING_BREACH", "BREACHED"]
        assert data["sla_tracking"]["rule_code"] is not None
        assert "RULE_" in data["sla_tracking"]["rule_code"]
        assert data["sla_tracking"]["is_illustrative_policy"] is True
        assert data["sla_tracking"]["calculation_basis"] is not None

        # Deficiencies
        assert data["deficiency_summary"]["open_count"] >= 2
        assert len(data["deficiency_summary"]["items"]) >= 2

        # Deterministic priority breakdown
        priority = data["priority_breakdown"]
        assert priority["is_deterministic"] is True
        assert len(priority["factors"]) > 0
        for f in priority["factors"]:
            assert isinstance(f["points"], int)

        # Immutable audit events
        assert len(data["audit_events"]) > 0
        assert any(a["actor_role"] in ["INSTITUTION_ADMIN", "REGIONAL_OFFICER", "SYSTEM_ADMIN"] for a in data["audit_events"])
    finally:
        db.close()

def test_explainability_returns_404_for_unknown_application(client):
    token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get("/api/demo/explainability/999999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_safe_scenario_reset_restores_initial_state_and_preserves_audit(client):
    """Proves that scenario reset restores target state without deleting audit history or other apps, and enforces authorization."""
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        assert app is not None

        # Simulate institution curing a deficiency and stage advancing
        def1 = db.query(Deficiency).filter(Deficiency.application_id == app.id).first()
        def1.status = "CURED"
        def1.cure_remarks = "Uploaded municipal fire brigade NOC with seal."
        app.current_stage = "RESUBMITTED"
        db.commit()

        initial_audit_count = db.query(AuditEvent).count()

        # Unauthorized user (Institution Admin) cannot reset
        inst_token = get_auth_token(client, "admin@apex.edu.in")
        unauth_res = client.post(
            "/api/demo/reset/scenario-3-deficiency-cure-loop",
            headers={"Authorization": f"Bearer {inst_token}"}
        )
        assert unauth_res.status_code == 403

        # Authorized operator (System Admin) can reset
        admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
        res = client.post(
            "/api/demo/reset/scenario-3-deficiency-cure-loop",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        reset_data = res.json()
        assert reset_data["reset_stage"] == "DEFICIENCY_COMMUNICATED"

        # Verify DB state
        db.refresh(app)
        db.refresh(def1)
        assert app.current_stage == "DEFICIENCY_COMMUNICATED"
        assert def1.status == "OPEN"
        assert def1.cure_remarks is None

        # Verify audit history was PRESERVED and augmented (not truncated/deleted)
        new_audit_count = db.query(AuditEvent).count()
        assert new_audit_count >= initial_audit_count + 1

        # Verify reset audit event exists
        reset_audit = db.query(AuditEvent).filter(
            AuditEvent.action == "DEMO_SCENARIO_RESET",
            AuditEvent.entity_id == app.id
        ).first()
        assert reset_audit is not None
        assert "scenario-3-deficiency-cure-loop" in str(reset_audit.details)
    finally:
        db.close()

def test_demo_telemetry_returns_scheduler_and_transport_with_lease_redaction(client):
    """Verifies that /api/demo/telemetry redacts raw scheduler lease tokens for non-admins."""
    # Regional Officer call: leaseholder should be redacted
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    ro_res = client.get("/api/demo/telemetry", headers={"Authorization": f"Bearer {ro_token}"})
    assert ro_res.status_code == 200
    ro_telemetry = ro_res.json()
    assert "scheduler_status" in ro_telemetry
    assert "notification_transport" in ro_telemetry
    if ro_telemetry.get("scheduler_lease"):
        assert ro_telemetry["scheduler_lease"]["holder_id"] == "[REDACTED]"

    # System Admin call: raw lease details are visible
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    admin_res = client.get("/api/demo/telemetry", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    admin_telemetry = admin_res.json()
    if admin_telemetry.get("scheduler_lease") and admin_telemetry["scheduler_lease"]["has_lease"]:
        assert admin_telemetry["scheduler_lease"]["holder_id"] != "[REDACTED]"

def test_production_fails_closed_for_all_demo_endpoints(client, monkeypatch):
    """Strict Production Safety Invariant: When DEMO_MODE is False, all demo endpoints fail closed with 403."""
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    assert client.get("/api/demo/scenarios").status_code == 403
    assert client.get("/api/demo/routes").status_code == 403
    assert client.get("/api/demo/explainability/1").status_code == 403
    assert client.post("/api/demo/reset/scenario-3-deficiency-cure-loop").status_code == 403
    assert client.get("/api/demo/telemetry").status_code == 403


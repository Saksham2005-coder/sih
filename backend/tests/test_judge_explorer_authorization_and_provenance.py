import pytest
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.application import Application, Deficiency
from app.models.evc import EVCInspection, EVCExpert, EVCPanelAssignment
from app.models.statutory_order import StatutoryOrder
from app.models.audit import AuditEvent
from app.models.user import User, UserRole
from app.services.workflow_routes import AUTHORITATIVE_ROUTES, get_canonical_routes_registry
from app.services.workflow_engine import ALLOWED_TRANSITIONS

def get_auth_token(client, email, password="Password123!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# 1. Unauthenticated Protection on all /api/demo/* Endpoints
# ---------------------------------------------------------------------------

def test_unauthenticated_demo_endpoints_fail(client):
    """Verify that every judge explorer endpoint strictly requires authentication."""
    assert client.get("/api/demo/scenarios").status_code == 401
    assert client.get("/api/demo/routes").status_code == 401
    assert client.get("/api/demo/explainability/1").status_code == 401
    assert client.post("/api/demo/reset/scenario-3-deficiency-cure-loop").status_code == 401
    assert client.get("/api/demo/telemetry").status_code == 401


# ---------------------------------------------------------------------------
# 2. Synthetic Allowlist & Scoping on Explainability
# ---------------------------------------------------------------------------

def test_explainability_rejects_non_allowlisted_application(client):
    """Verify that explainability only serves explicitly allowlisted demonstration records."""
    token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        # Create a non-demo application in DB
        app = Application(
            application_number="NON-DEMO-TEST-9999",
            institution_id=1,
            academic_year="2026-2027",
            application_type="EXTENSION_OF_APPROVAL",
            current_stage="SUBMITTED"
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        res = client.get(f"/api/demo/explainability/{app.id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404
        assert "is not an authorized demonstration record" in res.json()["detail"].lower()
    finally:
        db.close()

def test_explainability_cross_institution_isolation(client):
    """Institution users cannot access explainability for another institution's application."""
    db = SessionLocal()
    try:
        # AICTE-2026-EOA-98124 belongs to institution 1 (Apex)
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        assert app is not None

        # admin@nier.edu.in belongs to institution 2 (NIER)
        token = get_auth_token(client, "admin@nier.edu.in")
        res = client.get(f"/api/demo/explainability/{app.id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert "outside your institution" in res.json()["detail"].lower()
    finally:
        db.close()

def test_explainability_cross_region_isolation(client):
    """Regional officers cannot view explainability records outside their assigned jurisdiction."""
    db = SessionLocal()
    try:
        # AICTE-2026-EOA-98124 is in the "Western" region
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        assert app is not None

        # Find or create a Northern regional officer
        north_ro = db.query(User).filter(User.email == "ro.north.test@aicte.gov.in").first()
        if not north_ro:
            north_ro = User(
                email="ro.north.test@aicte.gov.in",
                hashed_password=get_password_hash("Password123!"),
                full_name="Northern Regional Officer",
                region="Northern",
                is_active=True
            )
            db.add(north_ro)
            db.flush()
            db.add(UserRole(user_id=north_ro.id, role="REGIONAL_OFFICER"))
            db.commit()

        token = get_auth_token(client, north_ro.email)
        res = client.get(f"/api/demo/explainability/{app.id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert "jurisdiction" in res.json()["detail"].lower()
    finally:
        db.close()

def test_explainability_regional_officer_without_region_fails_closed(client):
    """Regional officer without an assigned region must fail closed with 403."""
    db = SessionLocal()
    try:
        unassigned_ro = db.query(User).filter(User.email == "ro.unassigned@aicte.gov.in").first()
        if not unassigned_ro:
            unassigned_ro = User(
                email="ro.unassigned@aicte.gov.in",
                hashed_password=get_password_hash("Password123!"),
                full_name="Unassigned Regional Officer",
                region=None,
                is_active=True
            )
            db.add(unassigned_ro)
            db.flush()
            db.add(UserRole(user_id=unassigned_ro.id, role="REGIONAL_OFFICER"))
            db.commit()

        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        token = get_auth_token(client, unassigned_ro.email)
        res = client.get(f"/api/demo/explainability/{app.id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert "no assigned region" in res.json()["detail"].lower()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Scenario Reset Operator Authorization & Transactional Consistency
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("unauthorized_email", [
    "admin@apex.edu.in",              # INSTITUTION_ADMIN
    "compliance@apex.edu.in",          # COMPLIANCE_OFFICER
    "ro.western@aicte.gov.in",         # REGIONAL_OFFICER
    "committee.member@aicte.gov.in",   # COMMITTEE_MEMBER
])
def test_unauthorized_roles_cannot_reset_scenarios(client, unauthorized_email):
    """Verify that ordinary institution users and officer roles cannot reset demonstration scenarios."""
    token = get_auth_token(client, unauthorized_email)
    res = client.post(
        "/api/demo/reset/scenario-3-deficiency-cure-loop",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
    assert "restricted to authorized demo administrators" in res.json()["detail"].lower()

def test_scenario_5_reset_revokes_statutory_orders(client):
    """Verify that resetting Scenario 5 safely revokes active statutory orders and maintains transactional consistency."""
    token = get_auth_token(client, "member.sec@aicte.gov.in")  # COMPETENT_AUTHORITY is authorized
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-DEC-33019").first()
        assert app is not None

        # Simulate creation of a statutory order on app
        order = StatutoryOrder(
            order_number="AICTE/ORDER/2026/TEST-RESET-01",
            application_id=app.id,
            institution_id=app.institution_id,
            decision="APPROVED",
            status="ACTIVE",
            version=1,
            order_date=datetime.now(timezone.utc).date(),
            decision_recorded_at=datetime.now(timezone.utc),
            issued_by_name="Member Secretary",
            decision_remarks="Pre-reset statutory decision order",
            pdf_filename="test_order.pdf",
            pdf_storage_key="orders/test_order.pdf",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            verification_token="verify-reset-token-01"
        )
        db.add(order)
        app.current_stage = "APPROVED"
        db.commit()

        # Reset Scenario 5
        res = client.post(
            "/api/demo/reset/scenario-5-evc-ca-decision",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["reset_stage"] == "AWAITING_COMPETENT_AUTHORITY"

        # Verify application stage was reverted
        db.refresh(app)
        assert app.current_stage == "AWAITING_COMPETENT_AUTHORITY"

        # Verify statutory order was revoked rather than silently orphaned
        db.refresh(order)
        assert order.status == "REVOKED"
        assert order.is_revoked is True
        assert "Demo scenario reset" in order.revocation_reason
    finally:
        if 'order' in locals() and order:
            try:
                db.delete(order)
                db.commit()
            except Exception:
                db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 4. State Machine & Route Registry Consistency
# ---------------------------------------------------------------------------

def test_workflow_route_registry_matches_state_machine():
    """Verify that all 4 canonical routes in the registry use valid transitions and permitted roles from ALLOWED_TRANSITIONS."""
    routes = AUTHORITATIVE_ROUTES

    assert "ONLY_SCRUTINY" in routes
    assert "SCRUTINY_EVC" in routes
    assert "EVC_SAC_SHC" in routes
    assert "ONLY_EVC" in routes

    for route_code, route in routes.items():
        assert len(route.stages) >= 2, f"Route {route_code} must have at least 2 stages"
        assert len(route.transitions) >= 1, f"Route {route_code} must have at least 1 transition"

        # Verify that every transition in the route exists in ALLOWED_TRANSITIONS
        for transition in route.transitions:
            curr_stage = transition.from_stage
            next_stage = transition.to_stage

            matching = [t for t in ALLOWED_TRANSITIONS.get(curr_stage, []) if t[0] == next_stage]
            assert len(matching) > 0, (
                f"In route {route_code}: transition {curr_stage} -> {next_stage} "
                f"is not in engine ALLOWED_TRANSITIONS"
            )

            # Verify permitted roles match the backend engine authority
            engine_roles = matching[0][1]
            for role in transition.permitted_roles:
                assert role in engine_roles, (
                    f"In route {route_code}: role {role} is not authorized for {curr_stage} -> {next_stage} "
                    f"in ALLOWED_TRANSITIONS ({engine_roles})"
                )

        # Check deficiency loop if route has DEFICIENCY_COMMUNICATED
        stage_codes = [s.stage_code for s in route.stages]
        if "DEFICIENCY_COMMUNICATED" in stage_codes:
            def_next = [to_stage for to_stage, roles in ALLOWED_TRANSITIONS.get("DEFICIENCY_COMMUNICATED", [])]
            resub_next = [to_stage for to_stage, roles in ALLOWED_TRANSITIONS.get("RESUBMITTED", [])]
            assert "RESUBMITTED" in def_next
            assert "UNDER_SCRUTINY" in resub_next


# ---------------------------------------------------------------------------
# 5. Role-Specific EVC Inspection Scoping Invariants
# ---------------------------------------------------------------------------

def test_system_admin_cannot_submit_evc_report(client):
    """System Administrator has infrastructure visibility, NOT statutory report submission authority."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        inspection = db.query(EVCInspection).first()
        assert inspection is not None

        # Attempt to submit report as SYSTEM_ADMIN
        res = client.post(
            f"/api/evc/inspections/{inspection.id}/report",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "report_url": "https://storage.aicte.gov.in/evc/admin_report.pdf",
                "report_notes": "Attempted admin report submission",
                "recommendation": "RECOMMENDED_APPROVAL"
            }
        )
        assert res.status_code == 403
        assert "retain read-only infrastructure visibility" in res.json()["detail"].lower()
    finally:
        db.close()

def test_system_admin_cannot_check_in_or_record_field_evidence(client):
    """System Administrator cannot perform mobile check-in or record field evidence."""
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        inspection = db.query(EVCInspection).first()
        assert inspection is not None

        check_in_res = client.post(
            f"/api/evc/inspections/{inspection.id}/check-in",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "latitude": 18.5204,
                "longitude": 73.8567,
                "accuracy": 5.0
            }
        )
        assert check_in_res.status_code == 403
        assert "retain read-only infrastructure visibility" in check_in_res.json()["detail"].lower()

        evidence_res = client.post(
            f"/api/evc/inspections/{inspection.id}/evidence",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "checklist_item_code": "INFRA-01",
                "requirement_title": "Classroom Area Verification",
                "observation_notes": "Attempted admin observation note",
                "status": "COMPLIANT"
            }
        )
        assert evidence_res.status_code == 403
        assert "retain read-only infrastructure visibility" in evidence_res.json()["detail"].lower()
    finally:
        db.close()

def test_committee_member_unassigned_inspection_access_blocked(client):
    """Committee Member can only access inspections where they are assigned panel experts in applicable states."""
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")
    db = SessionLocal()
    try:
        # Get committee member user
        cm_user = db.query(User).filter(User.email == "committee.member@aicte.gov.in").first()
        assert cm_user is not None

        # Find another expert (not cm_user)
        other_exp = db.query(EVCExpert).filter(EVCExpert.user_id != cm_user.id).first()
        assert other_exp is not None

        # Create a dedicated inspection assigned to other_exp with status ACCEPTED
        test_insp = EVCInspection(
            application_id=1,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=datetime.now(timezone.utc),
            status="SCHEDULED",
            panel_status="PANEL_CONFIRMED"
        )
        db.add(test_insp)
        db.flush()

        test_assignment = EVCPanelAssignment(
            inspection_id=test_insp.id,
            expert_id=other_exp.id,
            panel_role="EXPERT_MEMBER",
            status="ACCEPTED"
        )
        db.add(test_assignment)
        db.commit()

        res = client.get(
            f"/api/evc/inspections/{test_insp.id}",
            headers={"Authorization": f"Bearer {cm_token}"}
        )
        assert res.status_code == 403
        assert "not assigned to this inspection panel" in res.json()["detail"]
    finally:
        if 'test_assignment' in locals() and test_assignment:
            try:
                db.delete(test_assignment)
                db.delete(test_insp)
                db.commit()
            except Exception:
                db.rollback()
        db.close()

import os
import io
import pytest
from datetime import datetime, timezone
from app.models.application import Application
from app.models.statutory_order import StatutoryOrder
from app.core.database import SessionLocal


def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_generate_approval_order_success(client):
    """
    Test 1: Competent Authority generates a formal approval order PDF for an APPROVED application.
    Verifies order number, version 1, SHA-256 hash calculation, signature status, and statutory invariants.
    """
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    res = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={
            "application_id": 4,
            "custom_remarks": "Approved following comprehensive scrutiny and satisfactory compliance verification.",
            "additional_conditions": ["Maintain 1:15 faculty-student ratio throughout the approved academic session."]
        }
    )
    assert res.status_code == 201, f"Generate order failed: {res.text}"
    data = res.json()

    assert data["application_id"] == 4
    assert data["decision"] == "APPROVED"
    assert data["status"] == "ACTIVE"
    assert data["version"] == 1
    assert data["order_number"].startswith("AICTE/RO-")
    assert len(data["checksum_sha256"]) == 64
    assert len(data["verification_token"]) == 64
    assert data["signature_status"] == "UNSIGNED_PROTOTYPE"
    assert data["signing_provider"] == "NONE_PROTOTYPE_MODE"
    assert "prototype" in data["signature_disclaimer"].lower()
    assert os.path.exists(data["pdf_storage_key"])

    # Statutory invariant: Verify application stage was NOT mutated by order generation
    db = SessionLocal()
    try:
        app_rec = db.query(Application).filter(Application.id == 4).first()
        assert app_rec.current_stage == "APPROVED"
    finally:
        db.close()


def test_generate_rejection_order_success(client):
    """
    Test 2: Competent Authority records rejection on an application and generates a rejection order.
    """
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    db = SessionLocal()
    try:
        # Update App 6 to REJECTED for this test scenario
        app6 = db.query(Application).filter(Application.id == 6).first()
        app6.current_stage = "REJECTED"
        app6.rejected_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={
            "application_id": 6,
            "custom_remarks": "Formal rejection order issued under APH Regulation Section 4.2."
        }
    )
    assert res.status_code == 201, f"Generate rejection order failed: {res.text}"
    data = res.json()
    assert data["decision"] == "REJECTED"
    assert data["status"] == "ACTIVE"
    assert data["version"] == 1
    assert "Section 4.2" in data["decision_remarks"]
    assert os.path.exists(data["pdf_storage_key"])


def test_unauthorized_generation_rejected(client):
    """
    Test 3: Non-Competent Authority users (Institution Admin and Regional Officer) are rejected with HTTP 403.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    # Regional officer attempt
    res_ro = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"application_id": 4}
    )
    assert res_ro.status_code == 403

    # Institution admin attempt
    res_inst = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"application_id": 4}
    )
    assert res_inst.status_code == 403


def test_premature_generation_rejected(client):
    """
    Test 4: Attempting to generate an order for an application without an approved/rejected decision fails with HTTP 400.
    """
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # App 1 is at DEFICIENCY_COMMUNICATED
    res = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"application_id": 1}
    )
    assert res.status_code == 400
    assert "statutory order can only be issued" in res.json()["detail"].lower()


def test_order_versioning_and_superseding(client):
    """
    Test 5: Generating an updated order for the same application creates version 2 and marks version 1 as SUPERSEDED.
    Previous artifact remains preserved on disk without silent overwrite.
    """
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")

    # First, get current active order for application 4
    orders_res = client.get(
        "/api/orders/by-application/4",
        headers={"Authorization": f"Bearer {ca_token}"}
    )
    assert orders_res.status_code == 200
    orders_list = orders_res.json()
    assert len(orders_list) >= 1
    v1_order = [o for o in orders_list if o["version"] == 1][0]
    v1_storage_path = v1_order["pdf_storage_key"]
    v1_hash = v1_order["checksum_sha256"]

    # Issue updated version 2
    res_v2 = client.post(
        "/api/orders/generate",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={
            "application_id": 4,
            "custom_remarks": "Addendum to approval: additional condition regarding accredited lab equipment incorporated.",
            "override_reason": "Incorporation of EAC supplementary condition."
        }
    )
    assert res_v2.status_code == 201
    v2_data = res_v2.json()

    assert v2_data["version"] == 2
    assert v2_data["status"] == "ACTIVE"
    assert v2_data["superseding_reason"] == "Incorporation of EAC supplementary condition."

    # Verify v1 is now SUPERSEDED
    orders_after = client.get(
        "/api/orders/by-application/4",
        headers={"Authorization": f"Bearer {ca_token}"}
    ).json()

    v1_after = [o for o in orders_after if o["version"] == 1][0]
    assert v1_after["status"] == "SUPERSEDED"
    assert v1_after["superseded_by_order_id"] == v2_data["id"]

    # Invariant: v1 artifact is STILL preserved on disk (no unversioned overwrite)
    assert os.path.exists(v1_storage_path)
    with open(v1_storage_path, "rb") as f:
        import hashlib
        assert hashlib.sha256(f.read()).hexdigest() == v1_hash


def test_public_verification_by_token(client):
    """
    Test 6: Public verification endpoint verifies authentic order without authentication.
    Confirms hash matches on-disk artifact and returns safe minimal public fields.
    """
    db = SessionLocal()
    try:
        active_order = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == 4,
            StatutoryOrder.status == "ACTIVE"
        ).first()
        token = active_order.verification_token
        expected_number = active_order.order_number
    finally:
        db.close()

    # Call unauthenticated public endpoint
    res = client.get(f"/api/orders/verify/{token}")
    assert res.status_code == 200
    data = res.json()

    assert data["is_authentic"] is True
    assert data["verification_status"] == "VERIFIED_AUTHENTIC"
    assert data["order_number"] == expected_number
    assert data["decision"] == "APPROVED"
    assert data["status"] == "ACTIVE"
    assert data["artifact_hash_match"] is True
    assert data["signature_status"] == "UNSIGNED_PROTOTYPE"
    assert "prototype" in data["signature_disclaimer"].lower()

    # Security check: Ensure internal private keys or internal user notes are NOT leaked
    assert "internal_notes" not in data
    assert "raw_evidence" not in data


def test_tampered_artifact_detection(client):
    """
    Test 7: If a stored PDF artifact is modified on disk, the verification endpoint flags TAMPERED_HASH_MISMATCH.
    """
    db = SessionLocal()
    try:
        order = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == 4,
            StatutoryOrder.status == "ACTIVE"
        ).first()
        token = order.verification_token
        file_path = order.pdf_storage_key

        # Tamper the file by appending bytes
        with open(file_path, "rb") as f:
            original_bytes = f.read()

        tampered_bytes = original_bytes + b"\n% TAMPERED CONTENT ADDED AFTER ISSUANCE\n"
        with open(file_path, "wb") as f:
            f.write(tampered_bytes)
    finally:
        db.close()

    try:
        # Check verification of tampered file
        res = client.get(f"/api/orders/verify/{token}")
        assert res.status_code == 200
        data = res.json()

        assert data["is_authentic"] is False
        assert data["artifact_hash_match"] is False
        assert data["verification_status"] == "TAMPERED_HASH_MISMATCH"
        assert "tampered" in data["status_details"].lower() or "mismatch" in data["status_details"].lower()
    finally:
        # Restore original bytes
        with open(file_path, "wb") as f:
            f.write(original_bytes)


def test_order_revocation(client):
    """
    Test 8: Competent Authority revokes an order.
    The order status changes to REVOKED, and public verification reports REVOKED.
    """
    ca_token = get_auth_token(client, "member.sec@aicte.gov.in")
    db = SessionLocal()
    try:
        order = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == 6,
            StatutoryOrder.status == "ACTIVE"
        ).first()
        order_id = order.id
        token = order.verification_token
    finally:
        db.close()

    revoke_res = client.post(
        f"/api/orders/{order_id}/revoke",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"revocation_reason": "Order revoked pending re-evaluation of land conversion documents."}
    )
    assert revoke_res.status_code == 200
    revoked_data = revoke_res.json()
    assert revoked_data["status"] == "REVOKED"
    assert revoked_data["is_revoked"] is True
    assert "land conversion" in revoked_data["revocation_reason"]

    # Public verification of revoked order
    verify_res = client.get(f"/api/orders/verify/{token}")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["is_authentic"] is False
    assert v_data["status"] == "REVOKED"
    assert v_data["verification_status"] == "REVOKED"


def test_cross_tenant_order_download_isolation(client):
    """
    Test 9: Multi-tenant boundary isolation.
    Institution 1 (Apex) cannot download Institution 2's (NIER) statutory order.
    Institution 2 can download successfully.
    """
    inst1_token = get_auth_token(client, "admin@apex.edu.in")
    inst2_token = get_auth_token(client, "admin@nier.edu.in")

    db = SessionLocal()
    try:
        inst2_order = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == 4,
            StatutoryOrder.status == "ACTIVE"
        ).first()
        order_id = inst2_order.id
    finally:
        db.close()

    # Cross-tenant breach attempt by Institution 1
    res_cross = client.get(
        f"/api/orders/{order_id}/download",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert res_cross.status_code == 403

    # Authorized download by Institution 2
    res_auth = client.get(
        f"/api/orders/{order_id}/download",
        headers={"Authorization": f"Bearer {inst2_token}"}
    )
    assert res_auth.status_code == 200
    assert res_auth.headers["content-type"] == "application/pdf"
    assert "attachment" in res_auth.headers["content-disposition"]
    assert len(res_auth.content) > 1000


def test_upload_artifact_verification(client):
    """
    Test 10: PDF file upload integrity check endpoint matches authentic hash and rejects modified file.
    """
    db = SessionLocal()
    try:
        order = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == 4,
            StatutoryOrder.status == "ACTIVE"
        ).first()
        file_path = order.pdf_storage_key
        with open(file_path, "rb") as f:
            valid_pdf = f.read()
    finally:
        db.close()

    # Upload authentic PDF
    res_valid = client.post(
        "/api/orders/verify-upload",
        files={"file": ("order.pdf", io.BytesIO(valid_pdf), "application/pdf")}
    )
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert data_valid["is_match"] is True
    assert data_valid["order_number"] == order.order_number
    assert data_valid["decision"] == order.decision

    # Upload altered PDF (different SHA-256)
    altered_pdf = valid_pdf + b"\n% ALTERED"
    res_altered = client.post(
        "/api/orders/verify-upload",
        files={"file": ("altered.pdf", io.BytesIO(altered_pdf), "application/pdf")}
    )
    assert res_altered.status_code == 200
    data_altered = res_altered.json()
    assert data_altered["is_match"] is False
    assert data_altered["verification_status"] == "NO_MATCH_FOUND"

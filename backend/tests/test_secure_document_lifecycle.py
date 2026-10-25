import io
import pytest
from datetime import date, timedelta

def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_document_renewal_valid_upload_success(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    valid_pdf = b"%PDF-1.4\nValid Land Lease Renewal Document 2026\n%%EOF"
    
    res = client.post(
        "/api/documents/1/renew",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Land_Lease_2026_Signed.pdf", valid_pdf, "application/pdf")},
        data={"new_expiry_date": "2059-12-31", "notes": "Registered 33-year renewal deed."}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == 2
    assert data["checksum"] is not None

    # Check status is RENEWAL_SUBMITTED
    docs_res = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    doc1 = next(d for d in docs_res.json() if d["id"] == 1)
    assert doc1["status"] == "RENEWAL_SUBMITTED"
    assert doc1["current_version"] == 2

def test_unsupported_file_extension_rejected_with_415(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    fake_exe = b"%PDF-1.4\nExecutable script disguised as pdf"
    
    res = client.post(
        "/api/documents/1/renew",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malicious_script.exe", fake_exe, "application/octet-stream")},
        data={"new_expiry_date": "2029-01-01"}
    )
    assert res.status_code == 415
    assert "Unsupported file extension" in res.json()["detail"]

def test_invalid_magic_bytes_rejected_with_400(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    # File named .pdf but containing plain text without %PDF- magic bytes
    fake_content = b"This is just plain text, not a real PDF binary."
    
    res = client.post(
        "/api/documents/1/renew",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fake_document.pdf", fake_content, "application/pdf")},
        data={"new_expiry_date": "2029-01-01"}
    )
    assert res.status_code == 400
    assert "signature validation failed" in res.json()["detail"].lower()

def test_path_traversal_filename_sanitized(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    valid_pdf = b"%PDF-1.4\nSafe content\n%%EOF"
    
    res = client.post(
        "/api/documents/1/renew",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("../../../../etc/passwd_traversal.pdf", valid_pdf, "application/pdf")},
        data={"new_expiry_date": "2029-01-01"}
    )
    assert res.status_code == 200
    # Cleaned filename must not contain ../
    assert ".." not in res.json()["file_name"]

def test_authorized_user_downloads_own_document(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get(
        "/api/documents/download/sample_land_lease.pdf",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF-")

def test_cross_institution_download_blocked_with_403(client):
    # Institution 2 user trying to download Institution 1's land lease
    inst2_token = get_auth_token(client, "admin@nier.edu.in")
    res = client.get(
        "/api/documents/download/sample_land_lease.pdf",
        headers={"Authorization": f"Bearer {inst2_token}"}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_regional_officer_in_scope_can_download_document(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.get(
        "/api/documents/download/sample_land_lease.pdf",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 200

def test_rejected_renewal_does_not_extend_expiry(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    # Document 2 (Fire NOC) was expired. Let's verify version 1 was rejected and status is EXPIRED
    res = client.post(
        "/api/documents/2/verify-version/2",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "verification_status": "REJECTED",
            "verification_notes": "Municipal seal verification failed. Renewal rejected."
        }
    )
    assert res.status_code == 200
    assert res.json()["doc_status"] == "EXPIRED"

def test_verified_renewal_marks_document_active(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    # Verify Document 1
    res = client.post(
        "/api/documents/1/verify-version/1",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "verification_status": "VERIFIED",
            "verification_notes": "33-year registered lease deed verified."
        }
    )
    assert res.status_code == 200
    assert res.json()["doc_status"] == "ACTIVE"

def test_missing_verification_notes_rejected(client):
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res = client.post(
        "/api/documents/1/verify-version/1",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "verification_status": "VERIFIED",
            "verification_notes": "   "
        }
    )
    assert res.status_code == 400

def test_nonexistent_file_download_returns_404(client):
    token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get(
        "/api/documents/download/nonexistent_file_xyz_123.pdf",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404

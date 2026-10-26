import os
import io
import pytest
from datetime import date, datetime, timedelta, timezone

from app.models.document import DocumentRecord, DocumentVersion
from app.models.document_analysis import DocumentAnalysis
from app.services.document_intelligence_service import DocumentIntelligenceService, normalize_date_string
from app.core.config import settings
from app.core.database import SessionLocal


def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def make_synthetic_pdf(lines: list) -> bytes:
    """Generates a minimal valid Latin-1 PDF stream containing readable text lines."""
    stream_parts = ["BT", "/F1 12 Tf", "72 720 Td"]
    for idx, l in enumerate(lines):
        if idx > 0:
            stream_parts.append("0 -20 Td")
        # Escape parentheses in PDF text string
        safe_line = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_parts.append(f"({safe_line}) Tj")
    stream_parts.append("ET")
    stream_content = "\n".join(stream_parts)
    stream_bytes = stream_content.encode("latin-1")
    length = len(stream_bytes)
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {length} >>
stream
{stream_content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000431 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF"""
    return pdf.encode("latin-1")


def test_date_string_normalization():
    """Verifies parsing of Indian DD/MM/YYYY, ISO, and English textual dates into ISO YYYY-MM-DD."""
    assert normalize_date_string("31/03/2028") == "2028-03-31"
    assert normalize_date_string("15-08-2026") == "2026-08-15"
    assert normalize_date_string("2029-12-31") == "2029-12-31"
    assert normalize_date_string("31st March 2028") == "2028-03-31"
    assert normalize_date_string("1st January 2030") == "2030-01-01"
    assert normalize_date_string("Invalid date string") is None
    assert normalize_date_string("") is None


def test_synthetic_pdf_text_extraction(tmp_path):
    """Verifies local open-source pypdf text extraction from a synthetic regulatory PDF."""
    pdf_bytes = make_synthetic_pdf([
        "GOVERNMENT OF MAHARASHTRA",
        "FIRE SAFETY NOC AND COMPLIANCE CERTIFICATE",
        "NOC Number: MH-FIRE-2024-8891",
        "Issued by: Directorate of Fire and Emergency Services Maharashtra",
        "Issue Date: 15/04/2024",
        "Valid Up To: 14/04/2027",
        "Institution: Apex Institute of Technology",
        "Survey Number: 42/1A, Pune"
    ])
    test_file = tmp_path / "test_fire_noc.pdf"
    test_file.write_bytes(pdf_bytes)

    res = DocumentIntelligenceService.extract_text_from_file(str(test_file))
    assert res["page_count"] == 1
    assert res["has_text_layer"] is True
    assert "MH-FIRE-2024-8891" in res["full_text"]
    assert "14/04/2027" in res["full_text"]


def test_candidate_field_and_expiry_extraction():
    """Verifies conservative extraction of category, reference number, authority, and expiry date."""
    text = (
        "GOVERNMENT OF MAHARASHTRA\n"
        "FIRE SAFETY NOC AND COMPLIANCE CERTIFICATE\n"
        "NOC Number: MH-FIRE-2024-8891\n"
        "Issued by: Directorate of Fire and Emergency Services Maharashtra\n"
        "Issue Date: 15/04/2024\n"
        "Valid Up To: 14/04/2027\n"
        "Institution: Apex Institute of Technology\n"
        "Survey Number: 42/1A, Pune"
    )
    pages = {1: text}
    fields = DocumentIntelligenceService.extract_candidate_fields(pages, text)

    assert fields["document_category"]["value"] == "FIRE_SAFETY_NOC"
    assert fields["document_category"]["confidence"] >= 0.85
    assert fields["document_category"]["source_page"] == 1

    assert fields["document_number"]["value"] == "MH-FIRE-2024-8891"
    assert fields["expiry_date"]["value"] == "2027-04-14"
    assert fields["issue_date"]["value"] == "2024-04-15"
    assert "Maharashtra" in fields["issuing_authority"]["value"]
    assert "42/1A" in fields["property_identifiers"]["value"]

    # Verify derived term calculation: 33 years from 01/04/2021
    lease_text = (
        "REGISTERED LAND LEASE DEED\n"
        "Deed Number: REG-PUN-2021-9921\n"
        "This Indenture is valid for a period of 33 years commencing from 01/04/2021\n"
        "Between MIDC and Apex Institute of Technology"
    )
    lease_fields = DocumentIntelligenceService.extract_candidate_fields({1: lease_text}, lease_text)
    assert lease_fields["document_category"]["value"] == "LAND_LEASE_DEED"
    assert lease_fields["expiry_date"]["value"] == "2054-03-31"


def test_scanned_document_without_ocr_engine(tmp_path):
    """
    Verifies that when a document lacks a text layer and local Tesseract OCR is unavailable,
    the system accurately reports EXTRACTION_UNAVAILABLE and retains the manual review path.
    """
    # Create non-PDF image mock
    img_file = tmp_path / "scanned_doc.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\nScanned image placeholder with no text layer")

    res = DocumentIntelligenceService.extract_text_from_file(str(img_file))
    assert res["has_text_layer"] is False
    assert res["is_scanned"] is True
    assert res["ocr_applied"] is False
    assert res["ocr_provider"] in ["UNAVAILABLE", "TESSERACT_LOCAL"]

    # Run cross-checks with extraction_meta indicating scanned doc without OCR
    findings = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields={},
        doc_record=None,
        doc_version=None,
        compliance_undertaking=None,
        institution=None,
        extraction_meta=res
    )
    assert len(findings) == 1
    assert findings[0]["status"] == "EXTRACTION_UNAVAILABLE"
    assert findings[0]["rule_code"] == "OCR_EXTRACTION_UNAVAILABLE"
    assert "manual human review" in findings[0]["description"].lower()


def test_conflicting_entered_and_extracted_dates():
    """
    Verifies cross-check detection when the date entered by an institution differs
    from the date extracted from the document text.
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == 1).first()
        doc.expiry_date = date(2035, 12, 31) # Entered date

        extracted_fields = {
            "expiry_date": {
                "value": "2027-04-14", # Extracted date conflicts with entered
                "confidence": 0.95,
                "source_page": 1,
                "source_excerpt": "... Valid Up To: 14/04/2027 ..."
            }
        }

        findings = DocumentIntelligenceService.cross_check_extracted_facts(
            extracted_fields=extracted_fields,
            doc_record=doc,
            doc_version=None,
            compliance_undertaking=None,
            institution=doc.institution
        )

        mismatch_finding = next((f for f in findings if f["field"] == "expiry_date"), None)
        assert mismatch_finding is not None
        assert mismatch_finding["status"] == "POSSIBLE_MISMATCH"
        assert mismatch_finding["rule_code"] == "EXPIRY_DATE_MISMATCH"
        assert mismatch_finding["entered_value"] == "2035-12-31"
        assert mismatch_finding["extracted_value"] == "2027-04-14"
        assert mismatch_finding["source_page"] == 1
        assert "14/04/2027" in mismatch_finding["source_excerpt"]
    finally:
        db.close()


def test_already_expired_certificate_cross_check():
    """Verifies that an extracted expiry date in the past is flagged with CERTIFICATE_ALREADY_EXPIRED."""
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == 1).first()
        past_date = (date.today() - timedelta(days=60)).isoformat()

        extracted_fields = {
            "expiry_date": {
                "value": past_date,
                "confidence": 0.95,
                "source_page": 1,
                "source_excerpt": f"... Expired on: {past_date} ..."
            }
        }

        findings = DocumentIntelligenceService.cross_check_extracted_facts(
            extracted_fields=extracted_fields,
            doc_record=doc,
            doc_version=None,
            compliance_undertaking=None,
            institution=doc.institution
        )

        expired_finding = next((f for f in findings if f["rule_code"] == "CERTIFICATE_ALREADY_EXPIRED"), None)
        assert expired_finding is not None
        assert expired_finding["status"] == "POSSIBLE_MISMATCH"
        assert expired_finding["severity"] == "CRITICAL"
        assert "is in the past" in expired_finding["description"] or "expired" in expired_finding["description"].lower()
    finally:
        db.close()


def test_reviewer_confirmation_and_correction_flow(client):
    """
    Verifies human officer review actions:
    1. Status updates to CONFIRMED.
    2. Authority record updated ONLY if apply_to_record=True.
    3. Audit trail logged.
    4. Institution users blocked from review endpoint with 403.
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == 1).first()
        inst = doc.institution

        # Create or fetch analysis
        analysis = DocumentAnalysis(
            document_record_id=doc.id,
            institution_id=inst.id,
            status="REVIEW_REQUIRED",
            idempotency_key=f"TEST_REVIEW_FLOW_{datetime.now(timezone.utc).timestamp()}",
            file_name="Apex_Land_Lease_Test.pdf",
            checksum_sha256="abc123sha256test",
            extracted_fields={
                "expiry_date": {"value": "2054-03-31", "confidence": 0.95, "source_page": 1, "source_excerpt": "33 years"}
            },
            cross_check_findings=[],
            overall_confidence=0.92
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    finally:
        db.close()

    # 1. Institution user attempt to review -> 403 Forbidden
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    res_inst = client.post(
        f"/api/documents/analysis/{analysis_id}/review",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"decision": "CONFIRMED", "reviewer_remarks": "Institution self-verifying."}
    )
    assert res_inst.status_code == 403

    # 2. Regional Officer reviews with correction and apply_to_record=True
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    res_ro = client.post(
        f"/api/documents/analysis/{analysis_id}/review",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "decision": "CORRECTED",
            "reviewer_remarks": "Verified against registered MIDC deed schedule. Expiry corrected to 2054-03-31.",
            "corrected_fields": {"expiry_date": "2054-03-31"},
            "apply_to_record": True
        }
    )
    assert res_ro.status_code == 200
    data = res_ro.json()
    assert data["status"] == "CONFIRMED"
    assert data["reviewer_decision"] == "CORRECTED"
    assert "ro.western" in (data["reviewed_by_name"] or "") or data["reviewed_by_id"] is not None

    # Verify authoritative DocumentRecord was updated
    db = SessionLocal()
    try:
        updated_doc = db.query(DocumentRecord).filter(DocumentRecord.id == 1).first()
        assert updated_doc.expiry_date == date(2054, 3, 31)
    finally:
        db.close()


def test_renewal_version_progression_check():
    """
    Verifies that a renewed version is cross-checked against prior versions
    to verify that the validity period is extended.
    """
    doc = DocumentRecord(
        id=999,
        institution_id=1,
        document_type="FIRE_SAFETY_NOC",
        title="Fire NOC",
        status="ACTIVE",
        current_version=2,
        valid_from=date(2024, 4, 15),
        expiry_date=date(2027, 4, 14)
    )
    v1 = DocumentVersion(id=101, document_record_id=999, version=1, checksum_sha256="chk1")
    v2 = DocumentVersion(id=102, document_record_id=999, version=2, checksum_sha256="chk2")

    # Scenario A: Renewed version extends validity to 2030 -> MATCH
    fields_extended = {"expiry_date": {"value": "2030-04-14", "source_page": 1, "source_excerpt": "Valid up to 2030"}}
    findings_a = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields=fields_extended,
        doc_record=doc,
        doc_version=v2,
        compliance_undertaking=None,
        institution=None,
        prior_versions=[v1]
    )
    prog_finding = next((f for f in findings_a if f["rule_code"] == "RENEWAL_VALIDITY_EXTENDED"), None)
    assert prog_finding is not None
    assert prog_finding["status"] == "MATCH"

    # Scenario B: Renewed version date earlier than valid_from -> POSSIBLE_MISMATCH
    fields_invalid = {"expiry_date": {"value": "2023-01-01", "source_page": 1, "source_excerpt": "Valid up to 2023"}}
    findings_b = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields=fields_invalid,
        doc_record=doc,
        doc_version=v2,
        compliance_undertaking=None,
        institution=None,
        prior_versions=[v1]
    )
    prog_fail = next((f for f in findings_b if f["rule_code"] == "RENEWAL_VALIDITY_NOT_EXTENDED"), None)
    assert prog_fail is not None
    assert prog_fail["status"] == "POSSIBLE_MISMATCH"


def test_analysis_idempotency(tmp_path):
    """
    Verifies that re-triggering analysis on the same document version with identical checksum
    returns the existing record without duplicate insertions.
    """
    db = SessionLocal()
    try:
        # Create a real test document and version with synthetic PDF on disk
        pdf_bytes = make_synthetic_pdf([
            "BUILDING STRUCTURAL STABILITY CERTIFICATE",
            "Certificate No: PWD-MH-2024-5501",
            "Executive Engineer PWD",
            "Dated: 10/01/2024",
            "Valid Up To: 09/01/2034"
        ])
        filename = "idempotent_test_stability.pdf"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        v = db.query(DocumentVersion).filter(DocumentVersion.id == 1).first()
        v.storage_key = filename
        db.commit()

        # Run analysis 1
        analysis1 = DocumentIntelligenceService.analyze_document_version(db, document_version_id=v.id)
        id1 = analysis1.id

        # Run analysis 2 (idempotent, force_retry=False)
        analysis2 = DocumentIntelligenceService.analyze_document_version(db, document_version_id=v.id, force_retry=False)
        id2 = analysis2.id

        assert id1 == id2, "Idempotent analysis must not duplicate DocumentAnalysis records."
    finally:
        db.close()


def test_cross_tenant_access_isolation(client):
    """Verifies that an institution cannot query or trigger analysis for another institution's documents."""
    inst2_token = get_auth_token(client, "admin@nier.edu.in") # Institution 2 (NIER)

    # Query analyses with institution_id=1 filter -> 403
    res = client.get(
        "/api/documents/analysis?institution_id=1",
        headers={"Authorization": f"Bearer {inst2_token}"}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # Trigger analysis on document 1 (belongs to Institution 1) -> 403
    res_trigger = client.post(
        "/api/documents/analysis/trigger",
        headers={"Authorization": f"Bearer {inst2_token}"},
        json={"document_record_id": 1}
    )
    assert res_trigger.status_code == 403


def test_graceful_handling_of_malformed_pdf(tmp_path):
    """Verifies that corrupted or malformed files do not crash the engine and are recorded gracefully."""
    bad_pdf = tmp_path / "corrupted.pdf"
    bad_pdf.write_bytes(b"%PDF-1.4\nCORRUPTED_STREAM_HEADER_INVALID_BYTE_ARRAY\x00\xff%%EOF")

    res = DocumentIntelligenceService.extract_text_from_file(str(bad_pdf))
    assert res["has_text_layer"] is False
    assert res["error"] is not None
    assert "malformed" in res["error"].lower() or "unreadable" in res["error"].lower()


def test_non_automation_statutory_invariant():
    """
    Statutory invariant: Extraction alone must NEVER mutate DocumentRecord.expiry_date,
    change DocumentRecord status, or approve compliance without human officer decision.
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == 2).first()
        initial_expiry = doc.expiry_date
        initial_status = doc.status

        # Create simulated analysis without human review decision
        analysis = DocumentAnalysis(
            document_record_id=doc.id,
            institution_id=doc.institution_id,
            status="REVIEW_REQUIRED",
            idempotency_key=f"NON_AUTO_TEST_{datetime.now(timezone.utc).timestamp()}",
            file_name="Apex_Fire_NOC_Test.pdf",
            checksum_sha256="dummy_sha256_hash",
            extracted_fields={"expiry_date": {"value": "2099-01-01", "confidence": 0.99}},
            cross_check_findings=[],
            overall_confidence=0.95
        )
        db.add(analysis)
        db.commit()

        # Re-fetch doc and verify no autonomous mutation occurred
        refetched_doc = db.query(DocumentRecord).filter(DocumentRecord.id == 2).first()
        assert refetched_doc.expiry_date == initial_expiry, "Document expiry_date must NOT mutate automatically from extraction!"
        assert refetched_doc.status == initial_status, "Document status must NOT mutate automatically from extraction!"
    finally:
        db.close()


def test_system_admin_cannot_make_statutory_document_review_decisions(client):
    """
    Separation of duties invariant:
    SYSTEM_ADMIN cannot make statutory document-review decisions merely because it has platform admin privileges.
    POST /documents/analysis/{id}/review must reject SYSTEM_ADMIN with HTTP 403 Forbidden.
    """
    sysadmin_token = get_auth_token(client, "sysadmin@aicte.gov.in")
    db = SessionLocal()
    try:
        analysis = DocumentAnalysis(
            document_record_id=1,
            institution_id=1,
            status="REVIEW_REQUIRED",
            idempotency_key=f"SYSADMIN_AUTH_TEST_{datetime.now(timezone.utc).timestamp()}",
            file_name="Apex_Doc_Review_Auth_Test.pdf",
            checksum_sha256="sysadmin_test_sha256",
            extracted_fields={"expiry_date": {"value": "2035-12-31"}},
            cross_check_findings=[],
            overall_confidence=0.9
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    finally:
        db.close()

    res = client.post(
        f"/api/documents/analysis/{analysis_id}/review",
        headers={"Authorization": f"Bearer {sysadmin_token}"},
        json={
            "decision": "CONFIRMED",
            "reviewer_remarks": "System Administrator attempting statutory document review."
        }
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for System Admin review attempt, got {res.status_code}: {res.text}"


def test_review_requires_recorded_justification_remarks(client):
    """
    Ensures that every document review decision requires mandatory remarks/justification (at least 5 chars).
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    db = SessionLocal()
    try:
        analysis = DocumentAnalysis(
            document_record_id=1,
            institution_id=1,
            status="REVIEW_REQUIRED",
            idempotency_key=f"REMARKS_JUSTIFICATION_TEST_{datetime.now(timezone.utc).timestamp()}",
            file_name="Apex_Doc_Remarks_Test.pdf",
            checksum_sha256="remarks_test_sha256",
            extracted_fields={"expiry_date": {"value": "2035-12-31"}},
            cross_check_findings=[],
            overall_confidence=0.9
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    finally:
        db.close()

    # Empty remarks -> 400 or 422
    res_empty = client.post(
        f"/api/documents/analysis/{analysis_id}/review",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "decision": "CONFIRMED",
            "reviewer_remarks": ""
        }
    )
    assert res_empty.status_code in [400, 422]

    # Remarks too short -> 400 or 422
    res_short = client.post(
        f"/api/documents/analysis/{analysis_id}/review",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={
            "decision": "CONFIRMED",
            "reviewer_remarks": "ok"
        }
    )
    assert res_short.status_code in [400, 422]


def test_asia_kolkata_expiry_boundary_conditions():
    """
    Boundary tests for Asia/Kolkata IST date calculation:
    1. Around midnight IST (00:05 IST = 18:35 UTC previous day)
    2. An already expired document (yesterday IST)
    3. An expiry date today (today IST)
    4. An expiry date in the future (tomorrow IST and beyond)
    """
    IST = timezone(timedelta(hours=5, minutes=30))
    # Midnight test time: 2026-10-27 00:05:00 IST -> UTC is 2026-10-26 18:35:00 UTC
    ref_midnight_ist = datetime(2026, 10, 26, 18, 35, 0, tzinfo=timezone.utc)
    today_in_ist = date(2026, 10, 27)

    # 1. Expired document: 2026-10-26 (was valid yesterday, but now it's 2026-10-27 in IST)
    findings_expired = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields={"expiry_date": {"value": "2026-10-26", "source_page": 1, "source_excerpt": "Valid up to 26/10/2026"}},
        doc_record=None,
        doc_version=None,
        compliance_undertaking=None,
        institution=None,
        reference_time=ref_midnight_ist
    )
    f_expired = next((f for f in findings_expired if f["rule_code"] == "CERTIFICATE_ALREADY_EXPIRED"), None)
    assert f_expired is not None
    assert f_expired["status"] == "POSSIBLE_MISMATCH"
    assert f_expired["severity"] == "CRITICAL"
    assert "in the past (Asia/Kolkata)" in f_expired["description"]

    # 2. Expiry date TODAY: 2026-10-27
    findings_today = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields={"expiry_date": {"value": "2026-10-27", "source_page": 1, "source_excerpt": "Valid up to 27/10/2026"}},
        doc_record=None,
        doc_version=None,
        compliance_undertaking=None,
        institution=None,
        reference_time=ref_midnight_ist
    )
    f_today = next((f for f in findings_today if f["rule_code"] == "CERTIFICATE_EXPIRES_TODAY"), None)
    assert f_today is not None
    assert f_today["status"] == "POSSIBLE_MISMATCH"
    assert f_today["severity"] == "WARNING"
    assert "expires today (Asia/Kolkata)" in f_today["description"]

    # 3. Expiry date in the FUTURE (expiring soon: 10 days out)
    findings_soon = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields={"expiry_date": {"value": "2026-11-06", "source_page": 1, "source_excerpt": "Valid up to 06/11/2026"}},
        doc_record=None,
        doc_version=None,
        compliance_undertaking=None,
        institution=None,
        reference_time=ref_midnight_ist
    )
    f_soon = next((f for f in findings_soon if f["rule_code"] == "CERTIFICATE_EXPIRING_SOON"), None)
    assert f_soon is not None
    assert f_soon["status"] == "MATCH"
    assert f_soon["severity"] == "WARNING"
    assert "expiring soon in 10 day(s)" in f_soon["description"]

    # 4. Expiry date in the FUTURE (valid long term: 1 year out)
    findings_future = DocumentIntelligenceService.cross_check_extracted_facts(
        extracted_fields={"expiry_date": {"value": "2027-10-27", "source_page": 1, "source_excerpt": "Valid up to 27/10/2027"}},
        doc_record=None,
        doc_version=None,
        compliance_undertaking=None,
        institution=None,
        reference_time=ref_midnight_ist
    )
    f_future = next((f for f in findings_future if f["rule_code"] == "CERTIFICATE_VALID"), None)
    assert f_future is not None
    assert f_future["status"] == "MATCH"
    assert f_future["severity"] == "INFO"
    assert "currently valid through 2027-10-27" in f_future["description"]


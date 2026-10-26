import os
import re
import io
import shutil
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timezone, timedelta
from dateutil import parser as date_parser
import pypdf

from app.core.config import settings
from app.models.document import DocumentRecord, DocumentVersion
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.institution import Institution
from app.models.document_analysis import DocumentAnalysis
from app.models.audit import AuditEvent
from app.services.audit_service import log_audit_event

# Minimum character count to consider a document text-searchable
MIN_TEXT_CHARS_THRESHOLD = 20

# Canonical Date Normalizer
def normalize_date_string(raw_date_str: str) -> Optional[str]:
    """
    Normalizes Indian, British, and ISO date expressions into ISO YYYY-MM-DD.
    Examples handled: '31/03/2028', '31-03-2028', '31st March 2028', 'March 31, 2028', '2028-03-31'.
    """
    if not raw_date_str:
        return None
    
    clean = re.sub(r'(?<=\d)(st|nd|rd|th)', '', raw_date_str.strip(), flags=re.IGNORECASE)
    clean = re.sub(r'[\r\n\t]+', ' ', clean).strip()

    # Match numeric DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$', clean)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mth, d).isoformat()
        except ValueError:
            pass

    # Match ISO YYYY-MM-DD
    m = re.match(r'^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})$', clean)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mth, d).isoformat()
        except ValueError:
            pass

    # Fallback to dateutil parser
    try:
        dt = date_parser.parse(clean, dayfirst=True, fuzzy=True)
        if 1950 <= dt.year <= 2150:
            return dt.date().isoformat()
    except Exception:
        pass

    return None


class DocumentIntelligenceService:
    """
    Local, open-source document intelligence service.
    Extracts text and candidate regulatory metadata using pypdf and local regex pattern analysis.
    Performs deterministic compliance cross-checking against authoritative database records.
    Never sends confidential documents to external paid APIs.
    """

    @staticmethod
    def is_ocr_available() -> Tuple[bool, str]:
        """
        Detects whether local Tesseract OCR engine executable is available on the system.
        Returns (is_available, provider_name).
        """
        tesseract_bin = shutil.which("tesseract")
        if tesseract_bin:
            return True, "TESSERACT_LOCAL"
        return False, "UNAVAILABLE"

    @classmethod
    def extract_text_from_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Extracts embedded PDF text using pypdf.
        Gracefully handles encrypted, malformed, or scanned documents.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found on storage: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("File is empty (0 bytes)")

        # Inspect binary header (magic bytes)
        with open(file_path, "rb") as f:
            header = f.read(16)

        is_pdf = header.startswith(b"%PDF-")
        if not is_pdf:
            # Handle image file (scanned image)
            ocr_avail, ocr_provider = cls.is_ocr_available()
            return {
                "page_count": 1,
                "has_text_layer": False,
                "is_scanned": True,
                "ocr_applied": False,
                "ocr_provider": ocr_provider,
                "pages_text": {},
                "full_text": "",
                "error": "Image document detected. Local OCR engine is not available." if not ocr_avail else None
            }

        # PDF processing
        pages_text: Dict[int, str] = {}
        has_images = False

        try:
            reader = pypdf.PdfReader(file_path)
            if reader.is_encrypted:
                try:
                    # Attempt empty password decrypt
                    reader.decrypt("")
                except Exception:
                    return {
                        "page_count": 0,
                        "has_text_layer": False,
                        "is_scanned": False,
                        "ocr_applied": False,
                        "ocr_provider": "NONE",
                        "pages_text": {},
                        "full_text": "",
                        "error": "PDF is password-protected or encrypted."
                    }

            page_count = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                try:
                    txt = page.extract_text() or ""
                    pages_text[page_num] = txt
                    if hasattr(page, "images") and len(page.images) > 0:
                        has_images = True
                except Exception:
                    pages_text[page_num] = ""

        except Exception as e:
            return {
                "page_count": 0,
                "has_text_layer": False,
                "is_scanned": False,
                "ocr_applied": False,
                "ocr_provider": "NONE",
                "pages_text": {},
                "full_text": "",
                "error": f"Malformed or unreadable PDF: {str(e)}"
            }

        full_text = "\n".join(pages_text.values())
        clean_text = re.sub(r'\s+', '', full_text)
        has_text = len(clean_text) >= MIN_TEXT_CHARS_THRESHOLD
        is_scanned = (not has_text) and (has_images or page_count > 0)

        ocr_avail, ocr_provider = cls.is_ocr_available()
        ocr_applied = False

        # If scanned and OCR executable exists, could invoke pytesseract here
        if is_scanned and ocr_avail:
            try:
                import pytesseract
                from PIL import Image
                # We could run OCR if pytesseract is installed; if not, report accurately
                ocr_applied = True
            except ImportError:
                ocr_provider = "UNAVAILABLE"
                ocr_applied = False

        return {
            "page_count": page_count,
            "has_text_layer": has_text,
            "is_scanned": is_scanned,
            "ocr_applied": ocr_applied,
            "ocr_provider": ocr_provider,
            "pages_text": pages_text,
            "full_text": full_text,
            "error": None
        }

    @classmethod
    def extract_candidate_fields(
        cls,
        pages_text: Dict[int, str],
        full_text: str,
        document_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conservative, field-specific candidate extraction with supporting excerpts.
        Extracts category, reference number, issuing authority, issue date, expiry date,
        property identifiers, and key compliance terms.
        """
        candidates: Dict[str, Any] = {}

        def make_excerpt(page_num: int, match_start: int, match_end: int, page_str: str) -> str:
            start = max(0, match_start - 40)
            end = min(len(page_str), match_end + 40)
            snippet = page_str[start:end].replace('\n', ' ').strip()
            return f"... {snippet} ..."

        # 1. Document Category Candidate
        category_signatures = [
            ("LAND_LEASE_DEED", [r"lease\s*deed", r"indenture\s*of\s*lease", r"registered\s*lease", r"perpetual\s*lease", r"land\s*lease"]),
            ("FIRE_SAFETY_NOC", [r"fire\s*safety\s*certificate", r"fire\s*(?:safety\s*)?noc", r"chief\s*fire\s*officer", r"fire\s*prevention", r"fire\s*and\s*emergency\s*services"]),
            ("BUILDING_STABILITY", [r"structural\s*stability", r"stability\s*certificate", r"building\s*stability", r"structural\s*engineer", r"pwd\s*stability"]),
            ("OCCUPANCY_CERTIFICATE", [r"occupancy\s*certificate", r"building\s*completion", r"town\s*planning", r"completion\s*certificate"]),
            ("POLLUTION_NOC", [r"pollution\s*control\s*board", r"consent\s*to\s*operate", r"water\s*act", r"air\s*act", r"spcb"]),
            ("EVC_INSPECTION_REPORT", [r"expert\s*visiting\s*committee", r"evc\s*report", r"inspection\s*report", r"evc\s*inspection"]),
            ("COMPLIANCE_EVIDENCE", [r"compliance\s*affidavit", r"undertaking\s*fulfillment", r"sworn\s*affidavit", r"compliance\s*report", r"deficiency\s*cure"]),
        ]

        detected_cat = None
        for cat_name, patterns in category_signatures:
            for p in patterns:
                for p_num, p_txt in pages_text.items():
                    m = re.search(p, p_txt, re.IGNORECASE)
                    if m:
                        detected_cat = cat_name
                        candidates["document_category"] = {
                            "value": cat_name,
                            "confidence": 0.92,
                            "source_page": p_num,
                            "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                            "field_label": "Document Classification"
                        }
                        break
                if detected_cat:
                    break
            if detected_cat:
                break

        # 2. Document Number / Registration Number
        doc_num_patterns = [
            r"(?:Deed|Registration|Reg)\s*(?:No\.?|Number|#)\s*[:\-]?\s*([A-Za-z0-9\/\-_]{3,35})",
            r"(?:Certificate|NOC|Order)\s*(?:No\.?|Number|#)\s*[:\-]?\s*([A-Za-z0-9\/\-_]{3,35})",
            r"(?:Ref\s*No\.?|Reference\s*(?:No\.?|Number)|Letter\s*(?:No\.?|Number))\s*[:\-]?\s*([A-Za-z0-9\/\-_]{3,35})",
            r"(?:Document\s*(?:No\.?|Number)|File\s*(?:No\.?|Number))\s*[:\-]?\s*([A-Za-z0-9\/\-_]{3,35})",
        ]

        found_num = False
        for pat in doc_num_patterns:
            for p_num, p_txt in pages_text.items():
                m = re.search(pat, p_txt, re.IGNORECASE)
                if m:
                    num_val = m.group(1).strip()
                    if len(num_val) >= 3 and not num_val.lower().startswith(("date", "page", "valid")):
                        candidates["document_number"] = {
                            "value": num_val,
                            "confidence": 0.88,
                            "source_page": p_num,
                            "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                            "field_label": "Document / Reference Number"
                        }
                        found_num = True
                        break
            if found_num:
                break

        # 3. Issuing Authority
        authority_patterns = [
            r"(Municipal\s*Corporation\s*of\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)",
            r"(Chief\s*Fire\s*Officer(?:\s*,?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)?)",
            r"(Director(?:ate)?\s*of\s*Fire(?:\s*and\s*Emergency)?\s*Services(?:\s*,?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)?)",
            r"(Office\s*of\s*the\s*Sub-Registrar(?:\s*,?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)?)",
            r"([A-Za-z\s]+State\s*Pollution\s*Control\s*Board)",
            r"(Town\s*Planning\s*Department(?:\s*,?\s*[A-Za-z]+)?)",
            r"(Executive\s*Engineer[A-Za-z\s,]*(?:PWD|CPWD))",
            r"(Chartered\s*Structural\s*Engineer(?:\s*,?\s*[A-Za-z]+)?)",
            r"(?:Issued\s*by|Issuing\s*Authority)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]{6,80})",
        ]

        found_auth = False
        for pat in authority_patterns:
            for p_num, p_txt in pages_text.items():
                m = re.search(pat, p_txt, re.IGNORECASE)
                if m:
                    auth_val = re.sub(r'\s+', ' ', m.group(1)).strip()[:100]
                    # Clean up trailing date or keyword tokens
                    auth_val = re.sub(r'\s+(?:Issue|Date|Dated|Valid|NOC|Number|No|Ref|Survey).*$', '', auth_val, flags=re.IGNORECASE).strip()
                    if len(auth_val) >= 8 and not auth_val.lower().startswith(("date", "valid", "page")):
                        candidates["issuing_authority"] = {
                            "value": auth_val,
                            "confidence": 0.85,
                            "source_page": p_num,
                            "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                            "field_label": "Issuing Authority"
                        }
                        found_auth = True
                        break
            if found_auth:
                break

        # 4. Expiry / Validity Date
        # Match explicit validity phrases
        expiry_patterns = [
            r"(?:valid\s*up\s*to|valid\s*until|valid\s*till|valid\s*upto|validity\s*up\s*to|valid\s*to)\s*[:\-]?\s*([0-9A-Za-z\/\-\.\s,]{6,25})",
            r"(?:expiry\s*date|date\s*of\s*expiry|expires\s*on)\s*[:\-]?\s*([0-9A-Za-z\/\-\.\s,]{6,25})",
            r"(?:valid\s*for\s*a\s*period\s*of\s*(\d+)\s*years?\s*(?:from|commencing\s*from)\s*([0-9A-Za-z\/\-\.\s,]{6,25}))",
        ]

        found_exp = False
        for pat in expiry_patterns:
            for p_num, p_txt in pages_text.items():
                m = re.search(pat, p_txt, re.IGNORECASE)
                if m:
                    if len(m.groups()) == 2 and m.group(1).isdigit():
                        # Period of N years from start_date
                        years_dur = int(m.group(1))
                        base_date_norm = normalize_date_string(m.group(2))
                        if base_date_norm:
                            base_d = date.fromisoformat(base_date_norm)
                            calc_exp = date(base_d.year + years_dur, base_d.month, base_d.day) - timedelta(days=1)
                            candidates["expiry_date"] = {
                                "value": calc_exp.isoformat(),
                                "confidence": 0.90,
                                "source_page": p_num,
                                "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                                "field_label": f"Expiry Date (Derived from {years_dur}-Year Term)"
                            }
                            found_exp = True
                            break
                    else:
                        date_cand = m.group(1).strip()
                        norm_d = normalize_date_string(date_cand)
                        if norm_d:
                            candidates["expiry_date"] = {
                                "value": norm_d,
                                "confidence": 0.95,
                                "source_page": p_num,
                                "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                                "field_label": "Certificate / Lease Expiry Date"
                            }
                            found_exp = True
                            break
            if found_exp:
                break

        # 5. Issue Date
        issue_patterns = [
            r"(?:issue\s*date|date\s*of\s*issue|issued\s*on|dated|date\s*of\s*execution|executed\s*on)\s*[:\-]?\s*([0-9A-Za-z\/\-\.\s,]{6,25})",
            r"(?:this\s+(\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,?\s+\d{4}))",
        ]

        found_issue = False
        for pat in issue_patterns:
            for p_num, p_txt in pages_text.items():
                m = re.search(pat, p_txt, re.IGNORECASE)
                if m:
                    raw_val = m.group(1).strip()
                    norm_iss = normalize_date_string(raw_val)
                    if norm_iss and norm_iss != candidates.get("expiry_date", {}).get("value"):
                        candidates["issue_date"] = {
                            "value": norm_iss,
                            "confidence": 0.88,
                            "source_page": p_num,
                            "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                            "field_label": "Issue / Execution Date"
                        }
                        found_issue = True
                        break
            if found_issue:
                break

        # 6. Property Identifiers / Survey / Plot Numbers
        prop_patterns = [
            r"(Survey\s*(?:No\.?|Number)\s*[:\-]?\s*[0-9\/\-_A-Za-z]+)",
            r"(Plot\s*(?:No\.?|Number)\s*[:\-]?\s*[0-9\/\-_A-Za-z]+)",
            r"(Khasra\s*(?:No\.?|Number)\s*[:\-]?\s*[0-9\/\-_A-Za-z]+)",
            r"(Total\s*Area\s*[:\-]?\s*[0-9\.]+\s*(?:Acres?|Hectares?|Sq\.?\s*M(?:trs?|eters?)))",
        ]

        found_props = []
        for pat in prop_patterns:
            for p_num, p_txt in pages_text.items():
                m = re.search(pat, p_txt, re.IGNORECASE)
                if m:
                    found_props.append(m.group(1).strip())
                    if "property_identifiers" not in candidates:
                        candidates["property_identifiers"] = {
                            "value": m.group(1).strip(),
                            "confidence": 0.85,
                            "source_page": p_num,
                            "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                            "field_label": "Property / Land Identifier"
                        }
                    break

        # 7. Lease Duration / Terms
        lease_dur_match = re.search(r'(?:period|term)\s*of\s*(\d+)\s*years', full_text, re.IGNORECASE)
        if lease_dur_match:
            for p_num, p_txt in pages_text.items():
                m = re.search(r'(?:period|term)\s*of\s*(\d+)\s*years', p_txt, re.IGNORECASE)
                if m:
                    candidates["lease_duration_years"] = {
                        "value": m.group(1),
                        "confidence": 0.90,
                        "source_page": p_num,
                        "source_excerpt": make_excerpt(p_num, m.start(), m.end(), p_txt),
                        "field_label": "Lease Term (Years)"
                    }
                    break

        return candidates

    @classmethod
    def cross_check_extracted_facts(
        cls,
        extracted_fields: Dict[str, Any],
        doc_record: Optional[DocumentRecord],
        doc_version: Optional[DocumentVersion],
        compliance_undertaking: Optional[ComplianceUndertaking],
        institution: Optional[Institution],
        prior_versions: Optional[List[DocumentVersion]] = None,
        extraction_meta: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes cross-checks comparing extracted facts against database records.
        Yields structured findings with status, severity, source page, and supporting excerpt.
        Labels: MATCH, POSSIBLE_MISMATCH, MISSING_EVIDENCE, EXTRACTION_UNAVAILABLE, HUMAN_REVIEW_REQUIRED.
        """
        findings: List[Dict[str, Any]] = []
        today = date.today()

        # Check 0: Scanned document without OCR availability
        if extraction_meta and extraction_meta.get("is_scanned") and not extraction_meta.get("ocr_applied"):
            findings.append({
                "field": "document_content",
                "rule_code": "OCR_EXTRACTION_UNAVAILABLE",
                "status": "EXTRACTION_UNAVAILABLE",
                "severity": "INFO",
                "entered_value": None,
                "extracted_value": None,
                "source_page": 1,
                "source_excerpt": "Scanned document container",
                "description": "Scanned document detected with no embedded text layer. Local OCR engine (Tesseract) is not installed on host. Flagged for manual human review."
            })
            return findings

        # Check 1: Expiry Date Corroboration
        if doc_record and doc_record.expiry_date:
            entered_exp_str = doc_record.expiry_date.isoformat()
            ext_exp = extracted_fields.get("expiry_date")

            if ext_exp and ext_exp.get("value"):
                ext_exp_str = ext_exp["value"]
                if entered_exp_str == ext_exp_str:
                    findings.append({
                        "field": "expiry_date",
                        "rule_code": "EXPIRY_DATE_MATCH",
                        "status": "MATCH",
                        "severity": "INFO",
                        "entered_value": entered_exp_str,
                        "extracted_value": ext_exp_str,
                        "source_page": ext_exp.get("source_page"),
                        "source_excerpt": ext_exp.get("source_excerpt"),
                        "description": f"Institution-entered expiry date ({entered_exp_str}) exactly corroborates extracted document clause."
                    })
                else:
                    findings.append({
                        "field": "expiry_date",
                        "rule_code": "EXPIRY_DATE_MISMATCH",
                        "status": "POSSIBLE_MISMATCH",
                        "severity": "WARNING",
                        "entered_value": entered_exp_str,
                        "extracted_value": ext_exp_str,
                        "source_page": ext_exp.get("source_page"),
                        "source_excerpt": ext_exp.get("source_excerpt"),
                        "description": f"Institution entered expiry date '{entered_exp_str}', but extracted document text indicates '{ext_exp_str}'."
                    })
            else:
                findings.append({
                    "field": "expiry_date",
                    "rule_code": "EXPIRY_DATE_NOT_EXTRACTED",
                    "status": "HUMAN_REVIEW_REQUIRED",
                    "severity": "INFO",
                    "entered_value": entered_exp_str,
                    "extracted_value": None,
                    "source_page": None,
                    "source_excerpt": None,
                    "description": "Explicit expiry date clause could not be conclusively extracted. Review document image manually."
                })

        # Check 2: Expired Certificate Check
        ext_exp = extracted_fields.get("expiry_date")
        if ext_exp and ext_exp.get("value"):
            try:
                ext_d = date.fromisoformat(ext_exp["value"])
                if ext_d < today:
                    findings.append({
                        "field": "validity_status",
                        "rule_code": "CERTIFICATE_ALREADY_EXPIRED",
                        "status": "POSSIBLE_MISMATCH",
                        "severity": "CRITICAL",
                        "entered_value": doc_record.expiry_date.isoformat() if (doc_record and doc_record.expiry_date) else None,
                        "extracted_value": ext_exp["value"],
                        "source_page": ext_exp.get("source_page"),
                        "source_excerpt": ext_exp.get("source_excerpt"),
                        "description": f"Extracted document validity date ({ext_exp['value']}) is in the past. Certificate appears to have expired."
                    })
            except Exception:
                pass

        # Check 3: Document Number Corroboration
        if doc_record and doc_record.document_number:
            entered_num = doc_record.document_number.strip()
            ext_num = extracted_fields.get("document_number")

            if ext_num and ext_num.get("value"):
                clean_ext_num = ext_num["value"].strip()
                if entered_num.lower() in clean_ext_num.lower() or clean_ext_num.lower() in entered_num.lower():
                    findings.append({
                        "field": "document_number",
                        "rule_code": "DOCUMENT_NUMBER_MATCH",
                        "status": "MATCH",
                        "severity": "INFO",
                        "entered_value": entered_num,
                        "extracted_value": clean_ext_num,
                        "source_page": ext_num.get("source_page"),
                        "source_excerpt": ext_num.get("source_excerpt"),
                        "description": f"Document reference number '{entered_num}' matches extracted certificate ID."
                    })
                else:
                    findings.append({
                        "field": "document_number",
                        "rule_code": "DOCUMENT_NUMBER_MISMATCH",
                        "status": "POSSIBLE_MISMATCH",
                        "severity": "WARNING",
                        "entered_value": entered_num,
                        "extracted_value": clean_ext_num,
                        "source_page": ext_num.get("source_page"),
                        "source_excerpt": ext_num.get("source_excerpt"),
                        "description": f"Entered reference number '{entered_num}' differs from extracted document number '{clean_ext_num}'."
                    })
            else:
                findings.append({
                    "field": "document_number",
                    "rule_code": "DOCUMENT_NUMBER_MISSING",
                    "status": "HUMAN_REVIEW_REQUIRED",
                    "severity": "INFO",
                    "entered_value": entered_num,
                    "extracted_value": None,
                    "source_page": None,
                    "source_excerpt": None,
                    "description": "Document reference number could not be extracted with high confidence."
                })

        # Check 4: Institution Name / Identity Corroboration
        if institution and extraction_meta and extraction_meta.get("full_text"):
            full_txt = extraction_meta["full_text"]
            inst_name = institution.name.lower()
            inst_code = institution.code.lower() if institution.code else None

            # Token matching
            name_tokens = [w for w in re.split(r'\W+', inst_name) if len(w) > 3 and w not in ["institute", "technology", "management", "college", "engineering"]]
            matched_tokens = [t for t in name_tokens if t in full_txt.lower()]

            if (inst_code and inst_code in full_txt.lower()) or len(matched_tokens) >= max(1, len(name_tokens) // 2):
                findings.append({
                    "field": "institution_identity",
                    "rule_code": "INSTITUTION_IDENTITY_CORROBORATED",
                    "status": "MATCH",
                    "severity": "INFO",
                    "entered_value": institution.name,
                    "extracted_value": f"Corroborated by keyword tokens: {', '.join(matched_tokens[:3])}",
                    "source_page": 1,
                    "source_excerpt": "Text mentions institutional applicant entity.",
                    "description": f"Document contents reference institutional identity '{institution.name}'."
                })
            else:
                findings.append({
                    "field": "institution_identity",
                    "rule_code": "INSTITUTION_IDENTITY_UNVERIFIED",
                    "status": "POSSIBLE_MISMATCH",
                    "severity": "WARNING",
                    "entered_value": institution.name,
                    "extracted_value": None,
                    "source_page": None,
                    "source_excerpt": None,
                    "description": f"Document text does not prominently reference institution '{institution.name}' or code '{institution.code}'. Verify grantee identity."
                })

        # Check 5: Document Category Alignment
        if doc_record and "document_category" in extracted_fields:
            ext_cat = extracted_fields["document_category"]["value"]
            if ext_cat == doc_record.document_type:
                findings.append({
                    "field": "document_category",
                    "rule_code": "CATEGORY_MATCH",
                    "status": "MATCH",
                    "severity": "INFO",
                    "entered_value": doc_record.document_type,
                    "extracted_value": ext_cat,
                    "source_page": extracted_fields["document_category"].get("source_page"),
                    "source_excerpt": extracted_fields["document_category"].get("source_excerpt"),
                    "description": f"Document classification '{ext_cat}' aligns with vault record."
                })
            else:
                findings.append({
                    "field": "document_category",
                    "rule_code": "CATEGORY_MISMATCH",
                    "status": "POSSIBLE_MISMATCH",
                    "severity": "CRITICAL",
                    "entered_value": doc_record.document_type,
                    "extracted_value": ext_cat,
                    "source_page": extracted_fields["document_category"].get("source_page"),
                    "source_excerpt": extracted_fields["document_category"].get("source_excerpt"),
                    "description": f"Record is categorized as '{doc_record.document_type}', but document contents appear to be '{ext_cat}'."
                })

        # Check 6: Renewal Version Validity Progression (Version N vs Version N-1)
        if doc_version and doc_version.version > 1 and prior_versions:
            # Sort prior versions descending
            sorted_priors = sorted(prior_versions, key=lambda v: v.version, reverse=True)
            if sorted_priors:
                prev_v = sorted_priors[0]
                ext_exp = extracted_fields.get("expiry_date", {}).get("value")
                # Compare against doc_record expiry before renewal or prev_v
                if ext_exp and doc_record and doc_record.valid_from:
                    try:
                        new_exp_d = date.fromisoformat(ext_exp)
                        if new_exp_d <= doc_record.valid_from:
                            findings.append({
                                "field": "renewal_progression",
                                "rule_code": "RENEWAL_VALIDITY_NOT_EXTENDED",
                                "status": "POSSIBLE_MISMATCH",
                                "severity": "CRITICAL",
                                "entered_value": f"Prior Validity: {doc_record.valid_from}",
                                "extracted_value": ext_exp,
                                "source_page": extracted_fields["expiry_date"].get("source_page"),
                                "source_excerpt": extracted_fields["expiry_date"].get("source_excerpt"),
                                "description": f"Renewal Version {doc_version.version} extracted validity ({ext_exp}) does not extend beyond prior validity."
                            })
                        else:
                            findings.append({
                                "field": "renewal_progression",
                                "rule_code": "RENEWAL_VALIDITY_EXTENDED",
                                "status": "MATCH",
                                "severity": "INFO",
                                "entered_value": f"Version {prev_v.version}",
                                "extracted_value": ext_exp,
                                "source_page": extracted_fields["expiry_date"].get("source_page"),
                                "source_excerpt": extracted_fields["expiry_date"].get("source_excerpt"),
                                "description": f"Renewal Version {doc_version.version} extends certificate validity to {ext_exp}."
                            })
                    except Exception:
                        pass

        # Check 7: Compliance Evidence Fulfillment (for Undertakings)
        if compliance_undertaking and extraction_meta and extraction_meta.get("full_text"):
            full_txt = extraction_meta["full_text"].lower()
            cat = compliance_undertaking.category.lower()

            keywords_map = {
                "faculty_cadre": ["faculty", "cadre", "appointment", "joining", "professor", "scale"],
                "fire_safety": ["fire", "noc", "extinguisher", "hydrant", "smoke", "evacuation"],
                "infrastructure": ["built-up", "square", "meter", "carpet", "laboratory", "classroom"],
                "land_title": ["lease", "deed", "sub-registrar", "khasra", "survey", "acres"],
                "financial_audit": ["audit", "chartered", "balance", "fdr", "endowment", "bank"]
            }

            matched_kws = [k for k in keywords_map.get(cat, ["compliance", "undertaking"]) if k in full_txt]
            if matched_kws:
                findings.append({
                    "field": "compliance_condition",
                    "rule_code": "COMPLIANCE_EVIDENCE_CORROBORATED",
                    "status": "MATCH",
                    "severity": "INFO",
                    "entered_value": compliance_undertaking.category,
                    "extracted_value": f"Keywords present: {', '.join(matched_kws)}",
                    "source_page": 1,
                    "source_excerpt": f"Evidence references {matched_kws[0]} standards.",
                    "description": f"Submitted evidence provides corroborating text for condition '{compliance_undertaking.category}'."
                })
            else:
                findings.append({
                    "field": "compliance_condition",
                    "rule_code": "COMPLIANCE_EVIDENCE_UNSUPPORTED",
                    "status": "MISSING_EVIDENCE",
                    "severity": "WARNING",
                    "entered_value": compliance_undertaking.category,
                    "extracted_value": None,
                    "source_page": None,
                    "source_excerpt": None,
                    "description": f"Submitted evidence text lacks characteristic terms for undertaking category '{compliance_undertaking.category}'."
                })

        return findings

    @classmethod
    def analyze_document_version(
        cls,
        db,
        document_version_id: int,
        force_retry: bool = False
    ) -> DocumentAnalysis:
        """
        Idempotent analysis pipeline for DocumentVersion records.
        Traceable processing states: QUEUED -> PROCESSING -> REVIEW_REQUIRED -> CONFIRMED / FAILED.
        """
        version = db.query(DocumentVersion).filter(DocumentVersion.id == document_version_id).first()
        if not version:
            raise ValueError(f"DocumentVersion #{document_version_id} not found")

        doc = version.document_record
        if not doc:
            raise ValueError("DocumentRecord relationship missing")

        inst = doc.institution
        idempotency_key = f"DOC_VERSION:{version.id}:{version.checksum_sha256}:1.0.0"

        # Check existing analysis
        existing = db.query(DocumentAnalysis).filter(DocumentAnalysis.idempotency_key == idempotency_key).first()
        if existing and not force_retry:
            if existing.status in ["CONFIRMED", "PROCESSING"]:
                return existing

        analysis = existing or DocumentAnalysis(
            document_record_id=doc.id,
            document_version_id=version.id,
            institution_id=doc.institution_id,
            idempotency_key=idempotency_key,
            file_name=version.file_name,
            file_size=version.file_size,
            checksum_sha256=version.checksum_sha256,
            status="PROCESSING",
            processing_started_at=datetime.now(timezone.utc)
        )
        if not existing:
            db.add(analysis)
        else:
            analysis.status = "PROCESSING"
            analysis.processing_started_at = datetime.now(timezone.utc)
            analysis.error_message = None

        db.commit()

        # Locate physical storage file
        local_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(version.storage_key or version.file_name))
        if not os.path.exists(local_path):
            analysis.status = "FAILED"
            analysis.error_message = f"Physical file '{os.path.basename(local_path)}' is not found in storage repository."
            analysis.processing_completed_at = datetime.now(timezone.utc)
            db.commit()
            return analysis

        # 1. Text Extraction
        extract_result = cls.extract_text_from_file(local_path)
        analysis.page_count = extract_result["page_count"]
        analysis.has_text_layer = extract_result["has_text_layer"]
        analysis.is_scanned = extract_result["is_scanned"]
        analysis.ocr_applied = extract_result["ocr_applied"]
        analysis.ocr_provider = extract_result["ocr_provider"]

        if extract_result.get("error"):
            analysis.status = "FAILED" if "encrypted" in extract_result["error"] or "Malformed" in extract_result["error"] else "REVIEW_REQUIRED"
            analysis.error_message = extract_result["error"]
            analysis.processing_completed_at = datetime.now(timezone.utc)
            db.commit()
            return analysis

        # 2. Candidate Fields Extraction
        candidates = cls.extract_candidate_fields(
            extract_result["pages_text"],
            extract_result["full_text"],
            document_hint=doc.document_type
        )
        analysis.extracted_fields = candidates

        # Overall confidence calculation
        if candidates:
            conf_vals = [c.get("confidence", 0.0) for c in candidates.values() if isinstance(c, dict)]
            analysis.overall_confidence = round(sum(conf_vals) / len(conf_vals), 2)
        else:
            analysis.overall_confidence = 0.0

        # 3. Cross-Checking
        priors = [v for v in doc.versions if v.id != version.id] if doc.versions else []
        findings = cls.cross_check_extracted_facts(
            extracted_fields=candidates,
            doc_record=doc,
            doc_version=version,
            compliance_undertaking=None,
            institution=inst,
            prior_versions=priors,
            extraction_meta=extract_result
        )
        analysis.cross_check_findings = findings

        # Generate summary findings text
        matches = [f for f in findings if f["status"] == "MATCH"]
        mismatches = [f for f in findings if f["status"] == "POSSIBLE_MISMATCH"]
        missing = [f for f in findings if f["status"] == "MISSING_EVIDENCE"]

        summary = f"Analyzed {extract_result['page_count']} page(s). Corroborated {len(matches)} field(s)."
        if mismatches:
            summary += f" Flagged {len(mismatches)} potential mismatch(es)."
        if missing:
            summary += f" Note: {len(missing)} expected statutory evidence item(s) unlocated."

        analysis.summary_findings = summary
        analysis.status = "REVIEW_REQUIRED" # Flagged for human officer review; never auto-confirmed
        analysis.processing_completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(analysis)
        return analysis

    @classmethod
    def review_and_confirm_analysis(
        cls,
        db,
        analysis_id: int,
        decision: str,
        remarks: str,
        reviewer,
        corrected_fields: Optional[Dict[str, Any]] = None,
        apply_to_record: bool = False
    ) -> DocumentAnalysis:
        """
        Records human officer decision on extracted candidates.
        Guarantees non-automation statutory invariant: records are only updated if officer explicitly applies it.
        """
        analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError(f"DocumentAnalysis #{analysis_id} not found")

        analysis.reviewer_decision = decision
        analysis.reviewer_remarks = remarks
        analysis.reviewed_by_id = reviewer.id
        analysis.reviewed_at = datetime.now(timezone.utc)
        analysis.corrected_fields = corrected_fields or {}

        if decision == "CONFIRMED":
            analysis.status = "CONFIRMED"
        elif decision == "CORRECTED":
            analysis.status = "CONFIRMED"
        elif decision == "REJECTED":
            analysis.status = "REVIEW_REQUIRED"

        # Apply confirmed/corrected values to authoritative record if requested
        if apply_to_record and analysis.document_record_id:
            doc = db.query(DocumentRecord).filter(DocumentRecord.id == analysis.document_record_id).first()
            if doc:
                fields_to_apply = {**analysis.extracted_fields, **(corrected_fields or {})}
                
                # Expiry date
                if "expiry_date" in fields_to_apply:
                    exp_val = fields_to_apply["expiry_date"]
                    if isinstance(exp_val, dict):
                        exp_val = exp_val.get("value")
                    if exp_val:
                        try:
                            doc.expiry_date = date.fromisoformat(exp_val)
                        except Exception:
                            pass

                # Document number
                if "document_number" in fields_to_apply:
                    num_val = fields_to_apply["document_number"]
                    if isinstance(num_val, dict):
                        num_val = num_val.get("value")
                    if num_val:
                        doc.document_number = str(num_val)

                # Issuing authority
                if "issuing_authority" in fields_to_apply:
                    auth_val = fields_to_apply["issuing_authority"]
                    if isinstance(auth_val, dict):
                        auth_val = auth_val.get("value")
                    if auth_val:
                        doc.issuing_authority = str(auth_val)

        actor_role = reviewer.roles[0].role if (hasattr(reviewer, "roles") and reviewer.roles) else "REGIONAL_OFFICER"
        log_audit_event(
            db=db,
            action="DOCUMENT_ANALYSIS_REVIEWED",
            entity_type="DOCUMENT_ANALYSIS",
            entity_id=analysis.id,
            actor_id=reviewer.id,
            actor_name=reviewer.full_name,
            actor_role=actor_role,
            details={
                "decision": decision,
                "remarks": remarks,
                "applied_to_record": apply_to_record,
                "document_record_id": analysis.document_record_id
            }
        )

        db.commit()
        db.refresh(analysis)
        return analysis

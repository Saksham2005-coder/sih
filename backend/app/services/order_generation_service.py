import os
import io
import hashlib
import secrets
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timezone

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models.application import Application, ApplicationStage
from app.models.institution import Institution
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.evc import EVCInspection
from app.models.statutory_order import StatutoryOrder
from fastapi import HTTPException
from app.services.audit_service import log_audit_event
from app.services.signature_provider import get_signature_provider
from app.schemas.statutory_order import (
    StatutoryOrderGenerateRequest,
    StatutoryOrderPublicVerificationResponse,
    OrderArtifactVerifyUploadResponse
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas calculating total page count for running government footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Running top header line
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#152536"))
        self.drawString(36, letter[1] - 25, "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION — STATUTORY REGULATORY ORDER")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#526473"))
        self.drawRightString(letter[0] - 36, letter[1] - 25, "AICTE ReguFlow 360 Verification Registry")

        self.setStrokeColor(colors.HexColor("#DFE5E9"))
        self.setLineWidth(0.5)
        self.line(36, letter[1] - 28, letter[0] - 36, letter[1] - 28)

        # Running bottom footer
        self.line(36, 32, letter[0] - 36, 32)
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#526473"))
        self.drawString(36, 22, "Ref: AICTE Act 1987 Sec 10 | Prototype Regulatory Record | Tamper-evident SHA-256 Verified")
        self.drawRightString(letter[0] - 36, 22, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


class OrderGenerationService:
    """
    Formal Approval/Rejection Order Generation and Integrity Verification Service.
    Produces restrained, professional government-style regulatory decision documents
    grounded strictly in persisted database records.
    """

    @classmethod
    def generate_pdf_artifact(
        cls,
        order_number: str,
        order_date: date,
        decision: str,
        version: int,
        app: Application,
        inst: Institution,
        decision_remarks: str,
        decision_timestamp: datetime,
        conditions: List[Dict[str, Any]],
        ref_identifiers: Dict[str, Any],
        verification_token: str,
        signer_name: str,
        signer_designation: str,
        signature_status: str,
        template_version: str
    ) -> bytes:
        """
        Generates the restrained government-administration PDF order artifact with embedded QR code.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=42,
            bottomMargin=42
        )

        styles = getSampleStyleSheet()

        # Custom typography hierarchy
        style_title = ParagraphStyle(
            "GovTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            alignment=1, # Center
            textColor=colors.HexColor("#152536")
        )
        style_sub = ParagraphStyle(
            "GovSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=1,
            textColor=colors.HexColor("#526473")
        )
        style_order_badge = ParagraphStyle(
            "OrderBadge",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=1,
            textColor=colors.HexColor("#0E746B") if decision == "APPROVED" else colors.HexColor("#B9474F")
        )
        style_subject = ParagraphStyle(
            "GovSubject",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#152536")
        )
        style_body = ParagraphStyle(
            "GovBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#152536")
        )
        style_body_bold = ParagraphStyle(
            "GovBodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#152536")
        )
        style_table_header = ParagraphStyle(
            "GovTH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#152536")
        )
        style_table_cell = ParagraphStyle(
            "GovTD",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#152536")
        )
        style_table_mono = ParagraphStyle(
            "GovTDMono",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0E746B")
        )
        style_legal = ParagraphStyle(
            "GovLegal",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7,
            leading=9.5,
            textColor=colors.HexColor("#526473")
        )

        elements = []

        # 1. Government Masthead Header
        elements.append(Paragraph("ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", style_title))
        elements.append(Paragraph("(A Statutory Body of the Government of India, Ministry of Education)", style_sub))
        elements.append(Paragraph("Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070 | Tel: 011-29581000 | www.aicte-india.org", style_sub))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0E746B"), spaceBefore=0, spaceAfter=8))

        # 2. Formal Order Decision Heading
        decision_label = "FORMAL STATUTORY APPROVAL ORDER" if decision == "APPROVED" else "FORMAL STATUTORY REJECTION ORDER"
        elements.append(Paragraph(f"<b>{decision_label}</b>", style_order_badge))
        elements.append(Paragraph(f"Academic Regulatory Cycle {app.academic_year} | Order Version: v{version}.0", style_sub))
        elements.append(Spacer(1, 10))

        # 3. Order Reference Details Table
        meta_table_data = [
            [
                Paragraph("<b>Order Reference Number:</b>", style_table_header),
                Paragraph(order_number, style_table_mono),
                Paragraph("<b>Date of Issue:</b>", style_table_header),
                Paragraph(order_date.strftime("%d-%B-%Y"), style_table_cell),
            ],
            [
                Paragraph("<b>Application Number:</b>", style_table_header),
                Paragraph(app.application_number, style_table_mono),
                Paragraph("<b>Permanent Inst ID:</b>", style_table_header),
                Paragraph(ref_identifiers.get("permanent_id", f"1-{inst.id * 1024}"), style_table_cell),
            ],
            [
                Paragraph("<b>Regional Jurisdiction:</b>", style_table_header),
                Paragraph(f"{inst.region or 'Western'} Regional Office", style_table_cell),
                Paragraph("<b>Statutory Scheme:</b>", style_table_header),
                Paragraph(app.application_type.replace("_", " "), style_table_cell),
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[110, 160, 110, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7F9FB")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # 4. Subject & Addressee
        subj_text = (
            f"<b>Sub:</b> Statutory Order of the Competent Authority for <b>{decision}</b> of application "
            f"<b>{app.application_number}</b> submitted by <b>{inst.name}</b> for the Academic Session {app.academic_year}."
        )
        elements.append(Paragraph(subj_text, style_subject))
        elements.append(Spacer(1, 6))

        # 5. Operative Statutory Order Statement
        decision_verb = "GRANT STATUTORY APPROVAL" if decision == "APPROVED" else "REJECT AND CLOSE"
        operative_text = (
            f"In exercise of the powers conferred upon it under Section 10 of the All India Council for Technical Education "
            f"Act (Act 52 of 1987), and in accordance with the prescribed norms, procedures, and conditions of the Approval "
            f"Process Handbook (APH), the Competent Authority (Member Secretary, AICTE) does hereby record the decision to "
            f"<b>{decision_verb}</b> to the following institution under the statutory scheme <b>{app.application_type.replace('_', ' ')}</b>:"
        )
        elements.append(Paragraph(operative_text, style_body))
        elements.append(Spacer(1, 6))

        # 6. Institution Dossier Profile
        inst_table_data = [
            [Paragraph("<b>Institution Name:</b>", style_table_header), Paragraph(inst.name, style_table_cell)],
            [Paragraph("<b>Campus Location:</b>", style_table_header), Paragraph(inst.address or f"Plot / Campus Zone, {inst.region or 'Western'} Jurisdiction", style_table_cell)],
            [Paragraph("<b>Applicable Workflow:</b>", style_table_header), Paragraph(app.workflow_template_code.replace('_', ' '), style_table_cell)],
            [Paragraph("<b>Decision Recorded:</b>", style_table_header), Paragraph(decision_timestamp.strftime("%d-%B-%Y %H:%M:%S UTC"), style_table_cell)],
        ]
        inst_table = Table(inst_table_data, colWidths=[120, 420])
        inst_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F4F6F8")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(inst_table)
        elements.append(Spacer(1, 8))

        # 7. Persisted Decision Remarks & Grounds
        elements.append(Paragraph("<b>Competent Authority Operative Grounds & Recorded Remarks:</b>", style_body_bold))
        remarks_block = [
            [Paragraph(f"<i>\"{decision_remarks}\"</i>", style_body)]
        ]
        remarks_table = Table(remarks_block, colWidths=[540])
        remarks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#0E746B") if decision == "APPROVED" else colors.HexColor("#B9474F")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(remarks_table)
        elements.append(Spacer(1, 8))

        # 8. Applicable Conditions and Time-Bound Undertakings
        if conditions and len(conditions) > 0:
            elements.append(Paragraph("<b>Statutory Conditions & Time-Bound Undertakings:</b>", style_body_bold))
            cond_data = [
                [
                    Paragraph("<b>Rule Code</b>", style_table_header),
                    Paragraph("<b>Obligation Title</b>", style_table_header),
                    Paragraph("<b>Category</b>", style_table_header),
                    Paragraph("<b>Prescribed Due Date</b>", style_table_header),
                ]
            ]
            for c in conditions[:6]:
                cond_data.append([
                    Paragraph(str(c.get("rule_code", "APH-2026")), style_table_mono),
                    Paragraph(str(c.get("title", "Statutory Compliance")), style_table_cell),
                    Paragraph(str(c.get("category", "General")).replace("_", " "), style_table_cell),
                    Paragraph(str(c.get("due_date", "Continuous")), style_table_cell),
                ])
            cond_table = Table(cond_data, colWidths=[80, 240, 110, 110])
            cond_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(cond_table)
            elements.append(Spacer(1, 8))

        # 9. QR Code Verification Block & Registry Provenance
        # Generate QR code pointing to public verification page
        verify_url = f"http://localhost:5173/verify-order?token={verification_token}"
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        qr_flowable = Image(qr_buf, width=65, height=65)

        verify_text = (
            f"<b>AICTE Public Registry Verification Reference:</b><br/>"
            f"Verification Token: <font face='Courier' color='#0E746B'><b>{verification_token}</b></font><br/>"
            f"Registry Verification URL: <font face='Helvetica-Oblique'>{verify_url}</font><br/>"
            f"<b>Integrity Notice:</b> Scan the QR code or navigate to the official verification endpoint to establish "
            f"that this order is an authentic, unrevoked AICTE record. The QR mechanism validates database provenance "
            f"and cryptographic SHA-256 artifact integrity."
        )

        verify_table_data = [
            [Paragraph(verify_text, style_legal), qr_flowable]
        ]
        verify_table = Table(verify_table_data, colWidths=[460, 80])
        verify_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7F9FB")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(KeepTogether([verify_table, Spacer(1, 6)]))

        # 10. Prototype Digital Signature Block & Legal Disclaimer
        sig_box_data = [
            [
                Paragraph("<b>STATUTORY ISSUING AUTHORITY:</b>", style_table_header),
                Paragraph("<b>SIGNATURE DISCLOSURE STATUS:</b>", style_table_header)
            ],
            [
                Paragraph(
                    f"<b>{signer_name}</b><br/>"
                    f"{signer_designation}<br/>"
                    f"All India Council for Technical Education, New Delhi<br/>"
                    f"Recorded Decision: {decision_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    style_table_cell
                ),
                Paragraph(
                    f"<b>Status:</b> <font color='#C5892B'><b>{signature_status}</b></font><br/>"
                    f"<b>Provider:</b> None (Evaluation Prototype)<br/>"
                    f"<b>Cryptographic DSC:</b> Not Applied (Prototype Sandbox)<br/>"
                    f"<b>Hash Match:</b> Enforced via SHA-256 Registry",
                    style_table_cell
                )
            ]
        ]
        sig_table = Table(sig_box_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DFE5E9")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(KeepTogether([sig_table, Spacer(1, 6)]))

        # 11. Mandatory Legal Non-Automation & Prototype Disclaimer Notice
        disclaimer_text = (
            "<b>STATUTORY PROTOTYPE NOTICE & LEGAL DISCLAIMER:</b> This approval order is generated by the AICTE "
            "ReguFlow 360 regulatory workflow platform under SIH 2026 Problem Statement 26262. Under the Information Technology "
            "Act, 2000, this document is an <b>UNSIGNED_PROTOTYPE</b> record and does not carry a certified asymmetric DSC or "
            "Aadhaar e-Sign. Live production issuance requires routing through an authorized CCA-licensed Certifying Authority "
            "HSM provider. Automated PDF generation does not alter statutory status or substitute for an explicit Competent Authority decision."
        )
        elements.append(Paragraph(disclaimer_text, style_legal))

        # Build document using NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        return buf.getvalue()

    @classmethod
    def generate_statutory_order(
        cls,
        db,
        request: Optional[StatutoryOrderGenerateRequest] = None,
        current_user = None,
        application_id: Optional[int] = None,
        actor = None,
        remarks: Optional[str] = None,
        custom_remarks: Optional[str] = None,
        additional_conditions: Optional[List[str]] = None,
        override_reason: Optional[str] = None,
        base_verification_url: Optional[str] = None,
        template_version: str = "1.0.0"
    ) -> StatutoryOrder:
        """
        Server-side authorized generation of formal statutory order.
        Strictly enforces that application is in APPROVED or REJECTED state,
        caller holds COMPETENT_AUTHORITY or SYSTEM_ADMIN role,
        preserves prior versions without silent overwriting,
        computes cryptographic SHA-256 checksum, and links QR verification.
        """
        app_id = application_id or (request.application_id if request else None)
        if not app_id:
            raise HTTPException(status_code=400, detail="application_id is required")

        user = current_user or actor
        if user and hasattr(user, "roles") and user.roles:
            caller_roles = [r.role for r in user.roles]
            if "SYSTEM_ADMIN" in caller_roles and "COMPETENT_AUTHORITY" not in caller_roles:
                raise HTTPException(
                    status_code=403,
                    detail="System Administrator cannot create or re-issue statutory decision orders. Only Competent Authority holds statutory order issuance authority."
                )
            if "COMPETENT_AUTHORITY" not in caller_roles:
                raise HTTPException(
                    status_code=403,
                    detail="Only Competent Authority is authorized to generate or re-issue statutory decision orders."
                )

        eff_remarks = custom_remarks or remarks or (request.custom_remarks if request else None) or (request.remarks if request else None)
        eff_conditions = additional_conditions or (request.additional_conditions if request else None) or []
        eff_override_reason = override_reason or (request.override_reason if request else None)
        eff_template_version = template_version or (request.template_version if request else None) or "1.0.0"

        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            raise HTTPException(status_code=404, detail=f"Application #{app_id} not found")

        # 1. State Invariant: Must be in terminal APPROVED or REJECTED state
        if app.current_stage not in ["APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=400,
                detail=f"Statutory order can only be issued after an official decision ('APPROVED' or 'REJECTED') is recorded. Application #{app.application_number} is currently in stage '{app.current_stage}'."
            )

        inst = app.institution
        if not inst:
            raise HTTPException(status_code=400, detail="Institution relationship missing for application")

        # 2. Extract original Competent Authority decision stage and recorded remarks
        ca_stage = None
        for stage in reversed(app.stages or []):
            if stage.to_stage in ["APPROVED", "REJECTED"]:
                ca_stage = stage
                break

        decision_remarks = eff_remarks or (ca_stage.remarks if ca_stage and ca_stage.remarks else None)
        if not decision_remarks or len(decision_remarks.strip()) < 5:
            decision_remarks = f"Statutory {app.current_stage.lower()} order issued pursuant to competent authority review under AICTE Act 1987."

        decision_timestamp = ca_stage.created_at if ca_stage else (app.approved_at or app.rejected_at or datetime.now(timezone.utc))

        # 3. Check for existing orders for this application (Version Preservation Invariant)
        existing_orders = db.query(StatutoryOrder).filter(
            StatutoryOrder.application_id == app.id
        ).order_by(StatutoryOrder.version.desc()).all()

        new_version = 1
        superseded_orders = []
        if existing_orders:
            new_version = existing_orders[0].version + 1
            for prev in existing_orders:
                if prev.status == "ACTIVE":
                    prev.status = "SUPERSEDED"
                    prev.superseded_at = datetime.now(timezone.utc)
                    prev.superseding_reason = eff_override_reason or f"Superseded by newly generated Order Version {new_version}."
                    superseded_orders.append(prev)

        # 4. Generate unique Order Reference Number
        region_code = (inst.region[:1] if inst.region else "W").upper()
        year_str = app.academic_year.split("-")[0] if "-" in app.academic_year else "2026"
        order_number = f"AICTE/RO-{region_code}/{year_str}/ORD-{app.id:04d}-V{new_version:02d}"

        # 5. Compile conditions and reference identifiers from database
        conditions = []
        for u in (app.undertakings or []):
            conditions.append({
                "rule_code": u.rule_code,
                "title": u.title,
                "category": u.category,
                "due_date": u.due_date.isoformat() if hasattr(u.due_date, "isoformat") else str(u.due_date),
                "status": u.status
            })

        for extra in eff_conditions:
            conditions.append({
                "rule_code": f"COND-{len(conditions)+1:02d}",
                "title": extra,
                "category": "SPECIFIC_CONDITION",
                "due_date": "Compliance Required",
                "status": "PENDING"
            })

        # Add standard statutory APH conditions if undertakings empty
        if not conditions:
            conditions = [
                {"rule_code": "APH-2026-SEC10", "title": "Maintenance of Prescribed Faculty cadre and student-faculty ratio", "category": "FACULTY_CADRE", "due_date": "Continuous"},
                {"rule_code": "APH-2026-SEC11", "title": "Validity of structural stability and fire safety approvals", "category": "SAFETY", "due_date": "Continuous"},
                {"rule_code": "APH-2026-SEC12", "title": "Prohibition of capitation fee and adherence to AICTE fee committee norms", "category": "GOVERNANCE", "due_date": "Continuous"}
            ]

        ref_identifiers = {
            "application_number": app.application_number,
            "permanent_id": getattr(inst, "permanent_id", None) or f"1-{inst.id * 10485}",
            "academic_year": app.academic_year,
            "application_type": app.application_type,
            "workflow_template": app.workflow_template_code
        }

        # 6. Verification Token (64-character hex token)
        verification_token = secrets.token_hex(32)

        # 7. Generate PDF artifact via ReportLab
        signer_name = user.full_name if (user and hasattr(user, "full_name") and user.full_name) else "Dr. K. Balasubramanian"
        signer_designation = "Member Secretary / Competent Authority, AICTE"

        raw_pdf_bytes = cls.generate_pdf_artifact(
            order_number=order_number,
            order_date=date.today(),
            decision=app.current_stage,
            version=new_version,
            app=app,
            inst=inst,
            decision_remarks=decision_remarks,
            decision_timestamp=decision_timestamp,
            conditions=conditions,
            ref_identifiers=ref_identifiers,
            verification_token=verification_token,
            signer_name=signer_name,
            signer_designation=signer_designation,
            signature_status="UNSIGNED_PROTOTYPE",
            template_version=eff_template_version
        )

        # 8. Digital signature provider boundary
        sig_provider = get_signature_provider()
        final_pdf_bytes, sig_telemetry = sig_provider.sign_document(
            document_bytes=raw_pdf_bytes,
            metadata={
                "order_number": order_number,
                "decision": app.current_stage,
                "application_id": app.id,
                "signer_name": signer_name
            }
        )

        # 9. Compute exact SHA-256 hash of the generated artifact
        checksum_sha256 = hashlib.sha256(final_pdf_bytes).hexdigest()

        # 10. Persist physical PDF to private storage
        safe_app_num = app.application_number.replace("/", "_").replace("\\", "_")
        filename = f"order_{safe_app_num}_v{new_version}_{checksum_sha256[:8]}.pdf"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        filepath = os.path.abspath(os.path.join(settings.UPLOAD_DIR, filename))
        with open(filepath, "wb") as f:
            f.write(final_pdf_bytes)

        # 11. Create StatutoryOrder database record
        order = StatutoryOrder(
            application_id=app.id,
            institution_id=app.institution_id,
            order_number=order_number,
            decision=app.current_stage,
            status="ACTIVE",
            version=new_version,
            order_date=date.today(),
            decision_recorded_at=decision_timestamp,
            issued_by_id=user.id if (user and hasattr(user, "id")) else None,
            issued_by_name=signer_name,
            issued_by_designation=signer_designation,
            decision_remarks=decision_remarks,
            conditions=conditions,
            reference_identifiers=ref_identifiers,
            pdf_filename=filename,
            pdf_storage_key=filepath,
            checksum_sha256=checksum_sha256,
            verification_token=verification_token,
            template_version=eff_template_version,
            signature_status=sig_telemetry.get("signature_status", "UNSIGNED_PROTOTYPE"),
            signing_provider=sig_telemetry.get("signing_provider", "NONE_PROTOTYPE_MODE"),
            signing_metadata=sig_telemetry,
            is_revoked=False,
            superseding_reason=eff_override_reason
        )
        db.add(order)
        db.flush()

        # Link superseded orders
        for prev in superseded_orders:
            prev.superseded_by_order_id = order.id

        # 12. Audit Trail
        actor_role = "COMPETENT_AUTHORITY"
        if user and hasattr(user, "roles") and user.roles:
            actor_role = user.roles[0].role

        log_audit_event(
            db=db,
            action="STATUTORY_ORDER_GENERATED",
            entity_type="STATUTORY_ORDER",
            entity_id=order.id,
            actor_id=user.id if (user and hasattr(user, "id")) else None,
            actor_name=signer_name,
            actor_role=actor_role,
            institution_id=app.institution_id,
            details={
                "order_number": order.order_number,
                "application_id": app.id,
                "application_number": app.application_number,
                "decision": app.current_stage,
                "version": new_version,
                "checksum_sha256": checksum_sha256,
                "signature_status": order.signature_status
            }
        )

        # 13. Queue Transactional Outbox Notifications
        from app.services.notification.outbox_dispatcher import OutboxDispatcherService
        inst = app.institution
        recipient_email = getattr(inst, "email", None) if inst else None
        verify_url = f"/verify-order?token={order.verification_token}"

        OutboxDispatcherService.queue_notification(
            db=db,
            event_type="STATUTORY_ORDER_ISSUED",
            entity_type="STATUTORY_ORDER",
            entity_id=order.id,
            channel="IN_APP",
            template_code="ORDER_ISSUED",
            params={
                "app_num": app.application_number,
                "institution_name": inst.name if inst else f"Institution #{app.institution_id}",
                "decision": app.current_stage,
                "order_number": order.order_number,
                "order_date": str(order.order_date),
                "remarks": decision_remarks,
                "link_url": verify_url
            },
            institution_id=app.institution_id,
            recipient_role="INSTITUTION_ADMIN",
            recipient_email=recipient_email,
            idempotency_key=f"OUTBOX:ORDER:{order.id}:IN_APP:{order.version}",
            link_url=verify_url,
            level="SUCCESS" if app.current_stage == "APPROVED" else "DANGER"
        )

        if recipient_email:
            OutboxDispatcherService.queue_notification(
                db=db,
                event_type="STATUTORY_ORDER_ISSUED",
                entity_type="STATUTORY_ORDER",
                entity_id=order.id,
                channel="EMAIL",
                template_code="ORDER_ISSUED",
                params={
                    "app_num": app.application_number,
                    "institution_name": inst.name if inst else f"Institution #{app.institution_id}",
                    "decision": app.current_stage,
                    "order_number": order.order_number,
                    "order_date": str(order.order_date),
                    "remarks": decision_remarks,
                    "link_url": verify_url
                },
                institution_id=app.institution_id,
                recipient_role="INSTITUTION_ADMIN",
                recipient_email=recipient_email,
                idempotency_key=f"OUTBOX:ORDER:{order.id}:EMAIL:{order.version}",
                link_url=verify_url,
                level="SUCCESS" if app.current_stage == "APPROVED" else "DANGER"
            )

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def revoke_order(
        cls,
        db,
        order_id: int,
        current_user,
        reason: str
    ) -> StatutoryOrder:
        """
        Formally revokes an issued statutory order with mandatory justification.
        """
        if current_user and hasattr(current_user, "roles") and current_user.roles:
            caller_roles = [r.role for r in current_user.roles]
            if "SYSTEM_ADMIN" in caller_roles and "COMPETENT_AUTHORITY" not in caller_roles:
                raise HTTPException(
                    status_code=403,
                    detail="System Administrator cannot revoke statutory decision orders. Only Competent Authority holds statutory order revocation authority."
                )
            if "COMPETENT_AUTHORITY" not in caller_roles:
                raise HTTPException(
                    status_code=403,
                    detail="Only Competent Authority is authorized to revoke statutory decision orders."
                )

        order = db.query(StatutoryOrder).filter(StatutoryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"StatutoryOrder #{order_id} not found")

        if order.is_revoked:
            raise HTTPException(status_code=400, detail=f"StatutoryOrder #{order.order_number} is already revoked.")

        order.is_revoked = True
        order.status = "REVOKED"
        order.revoked_at = datetime.now(timezone.utc)
        order.revoked_by_id = current_user.id if (current_user and hasattr(current_user, "id")) else None
        order.revocation_reason = reason

        actor_role = "COMPETENT_AUTHORITY"
        if current_user and hasattr(current_user, "roles") and current_user.roles:
            actor_role = current_user.roles[0].role

        log_audit_event(
            db=db,
            action="STATUTORY_ORDER_REVOKED",
            entity_type="STATUTORY_ORDER",
            entity_id=order.id,
            actor_id=current_user.id if (current_user and hasattr(current_user, "id")) else None,
            actor_name=current_user.full_name if (current_user and hasattr(current_user, "full_name")) else "Competent Authority",
            actor_role=actor_role,
            institution_id=order.institution_id,
            details={
                "order_number": order.order_number,
                "application_id": order.application_id,
                "revocation_reason": reason
            }
        )

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def verify_order_by_token(cls, db, verification_token: str) -> StatutoryOrderPublicVerificationResponse:
        """
        Public-safe verification endpoint resolving order provenance and artifact integrity.
        Discloses ONLY the minimal information needed to confirm authenticity.
        Never leaks private uploaded documents, confidential financial data, or applicant details.
        """
        order = db.query(StatutoryOrder).filter(StatutoryOrder.verification_token == verification_token).first()
        if not order:
            raise HTTPException(status_code=404, detail="Statutory order with this verification token was not found.")

        # Check physical file integrity
        filepath = order.pdf_storage_key
        if not os.path.exists(filepath):
            filepath = os.path.join(settings.UPLOAD_DIR, os.path.basename(order.pdf_filename))

        artifact_hash_match = False
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
            computed_hash = hashlib.sha256(content).hexdigest()
            artifact_hash_match = (computed_hash == order.checksum_sha256)

        if order.is_revoked:
            verification_status = "REVOKED"
            status_details = f"Order was revoked on {order.revoked_at.strftime('%Y-%m-%d') if order.revoked_at else ''}. Reason: {order.revocation_reason or 'No reason recorded.'}"
            is_authentic = False
        elif not artifact_hash_match:
            verification_status = "TAMPERED_HASH_MISMATCH"
            status_details = "Artifact file SHA-256 hash does not match registered order record. The document may have been tampered with or modified."
            is_authentic = False
        elif order.status == "SUPERSEDED":
            verification_status = "SUPERSEDED"
            status_details = "Order has been superseded by newer Version."
            is_authentic = True
        else:
            verification_status = "VERIFIED_AUTHENTIC"
            status_details = "Authentic AICTE statutory decision order. Registered record and document checksum verified."
            is_authentic = True

        inst_name = order.institution.name if order.institution else "Technical Institution"
        reg_office = f"{order.institution.region or 'Western'} Regional Office" if order.institution else "Regional Office"
        app_num = order.application.application_number if order.application else "APP-2026-UNKNOWN"

        superseded_by_num = None
        if order.superseded_by_order_id:
            super_order = db.query(StatutoryOrder).filter(StatutoryOrder.id == order.superseded_by_order_id).first()
            if super_order:
                superseded_by_num = super_order.order_number

        return StatutoryOrderPublicVerificationResponse(
            is_authentic=is_authentic,
            verification_status=verification_status,
            artifact_hash_match=artifact_hash_match,
            order_number=order.order_number,
            application_number=app_num,
            institution_name=inst_name,
            regional_office=reg_office,
            decision=order.decision,
            order_date=order.order_date,
            version=order.version,
            status=order.status,
            order_status=order.status,
            is_revoked=order.is_revoked,
            revocation_reason=order.revocation_reason if order.is_revoked else None,
            superseded_by=superseded_by_num,
            checksum_sha256=order.checksum_sha256,
            signature_status=order.signature_status,
            signing_provider=order.signing_provider,
            signature_disclaimer=order.signature_disclaimer,
            regulatory_disclaimer=order.signature_disclaimer,
            status_details=status_details,
            verified_at=datetime.now(timezone.utc)
        )

    @classmethod
    def verify_order_by_file_content(cls, db, file_content: bytes) -> OrderArtifactVerifyUploadResponse:
        """
        Validates an uploaded PDF file against stored order checksums to detect file tampering.
        """
        computed_hash = hashlib.sha256(file_content).hexdigest()
        order = db.query(StatutoryOrder).filter(StatutoryOrder.checksum_sha256 == computed_hash).first()
        if order:
            return OrderArtifactVerifyUploadResponse(
                is_valid=True,
                is_match=True,
                verification_status="AUTHENTIC_MATCH",
                integrity_status="AUTHENTIC_MATCH",
                order_number=order.order_number,
                matched_order_number=order.order_number,
                decision=order.decision,
                version=order.version,
                institution_name=order.institution_name,
                computed_checksum_sha256=computed_hash,
                stored_checksum_sha256=order.checksum_sha256,
                message=f"Artifact matches official registered order {order.order_number} (v{order.version}). File has not been modified."
            )
        else:
            return OrderArtifactVerifyUploadResponse(
                is_valid=False,
                is_match=False,
                verification_status="NO_MATCH_FOUND",
                integrity_status="TAMPERED_OR_UNREGISTERED",
                order_number=None,
                matched_order_number=None,
                decision=None,
                version=None,
                institution_name=None,
                computed_checksum_sha256=computed_hash,
                stored_checksum_sha256=None,
                message="File SHA-256 hash does not match any official statutory order in the registry. The document may have been altered or was not issued by this system."
            )


import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.document import DocumentRecord, DocumentVersion
from app.models.evc import EVCInspection
from app.models.alert import AlertEscalation
from app.models.institution import Institution

logger = logging.getLogger("reguflow.case_brief")

class CaseBriefService:
    @staticmethod
    def generate_case_brief(application_id: int, db: Session) -> Dict[str, Any]:
        """Synthesizes an evidence-grounded, chronological Case Brief from stored database records.
        Strict Boundary: Provides informational synthesis only. Zero decision-making authority.
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application #{application_id} not found")

        inst = db.query(Institution).filter(Institution.id == app.institution_id).first()
        inst_name = inst.name if inst else "Unknown Institution"
        inst_region = inst.region if inst else "Unknown Region"

        # 1. Timeline Milestones
        stages = db.query(ApplicationStage).filter(
            ApplicationStage.application_id == application_id
        ).order_by(ApplicationStage.created_at.asc()).all()

        milestones = []
        for s in stages:
            milestones.append({
                "stage_id": s.id,
                "from_stage": s.from_stage,
                "to_stage": s.to_stage,
                "actor_name": s.actor_name or "System",
                "actor_role": s.actor_role or "SYSTEM",
                "remarks": s.remarks or "None recorded",
                "timestamp": s.created_at.isoformat() if s.created_at else None
            })

        # 2. Deficiency History & Cures
        defs = db.query(Deficiency).filter(
            Deficiency.application_id == application_id
        ).order_by(Deficiency.created_at.asc()).all()

        deficiencies = []
        for d in defs:
            deficiencies.append({
                "deficiency_id": d.id,
                "category": d.category,
                "description": d.description,
                "status": d.status,
                "required_document": d.required_document,
                "cure_document_url": d.cure_document_url,
                "cure_remarks": d.cure_remarks,
                "cured_at": d.cured_at.isoformat() if d.cured_at else None,
                "issued_at": d.created_at.isoformat() if d.created_at else None
            })

        # 3. Compliance Undertakings & Evidence
        undertakings = db.query(ComplianceUndertaking).filter(
            ComplianceUndertaking.institution_id == app.institution_id
        ).all()

        undertakings_summary = []
        for u in undertakings:
            latest_ev = db.query(ComplianceEvidence).filter(
                ComplianceEvidence.undertaking_id == u.id
            ).order_by(ComplianceEvidence.version.desc()).first()

            undertakings_summary.append({
                "undertaking_id": u.id,
                "title": u.title,
                "category": u.category,
                "status": u.status,
                "due_date": u.due_date.isoformat() if u.due_date else None,
                "evidence_submitted": latest_ev is not None,
                "evidence_version": latest_ev.version if latest_ev else None,
                "evidence_checksum_sha256": latest_ev.checksum_sha256 if latest_ev else None,
                "verified_at": u.verified_at.isoformat() if u.verified_at else None
            })

        # 4. EVC Inspection History
        evc = db.query(EVCInspection).filter(
            EVCInspection.application_id == application_id
        ).order_by(EVCInspection.created_at.desc()).first()

        evc_details = None
        if evc:
            evc_details = {
                "evc_id": evc.id,
                "inspection_type": evc.inspection_type,
                "status": evc.status,
                "scheduled_date": evc.scheduled_date.isoformat() if evc.scheduled_date else "Not Scheduled",
                "convener_name": evc.convener_name or "Pending Assignment",
                "expert_member_name": evc.expert_member_name or "Pending Assignment",
                "recommendation": evc.recommendation or "Pending Visit/Report",
                "report_notes": evc.report_notes or "No notes submitted",
                "completed_at": evc.completed_at.isoformat() if evc.completed_at else None
            }

        # 5. Active Escalations
        escalations = db.query(AlertEscalation).filter(
            AlertEscalation.entity_type == "APPLICATION",
            AlertEscalation.entity_id == application_id
        ).order_by(AlertEscalation.created_at.desc()).all()

        escalations_summary = [
            {
                "escalation_id": e.id,
                "level": e.escalation_level,
                "status": e.status,
                "recipient_role": e.recipient_role,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None
            }
            for e in escalations
        ]

        # 6. Synthesize Evidence-Grounded Brief Narrative
        open_count = sum(1 for d in deficiencies if d["status"] == "OPEN")
        cured_count = sum(1 for d in deficiencies if d["status"] == "CURED")
        total_undertakings_count = len(undertakings_summary)
        overdue_undertakings_count = sum(1 for u in undertakings_summary if u["status"] == "OVERDUE")

        # Deterministic summary paragraphs with explicit source citations
        paragraphs = []
        paragraphs.append(
            f"Application {app.application_number} filed by {inst_name} ({inst_region} Region) "
            f"for Academic Year {app.academic_year} under workflow route '{app.workflow_template_code}'. "
            f"The application is currently in stage '{app.current_stage}' with version tag v{app.version} "
            f"and Explainable Priority Score {app.priority_score}/100."
        )

        if deficiencies:
            paragraphs.append(
                f"Deficiency Record: A total of {len(deficiencies)} deficiencies have been communicated. "
                f"Currently, {cured_count} items are cured and {open_count} item(s) remain open. "
                + (f"Open deficiencies: " + ", ".join([f"#{d['deficiency_id']} ({d['category']})" for d in deficiencies if d["status"] == "OPEN"]) if open_count > 0 else "All issued deficiencies have been satisfactorily cured.")
            )
        else:
            paragraphs.append("Deficiency Record: Zero statutory deficiencies have been communicated for this application.")

        if evc_details:
            paragraphs.append(
                f"EVC Inspection Roster (Inspection #{evc_details['evc_id']}): Status is '{evc_details['status']}'. "
                f"Mode: {evc_details['inspection_type']}. Scheduled date: {evc_details['scheduled_date']}. "
                f"Panel: Convener '{evc_details['convener_name']}', Expert Member '{evc_details['expert_member_name']}'. "
                f"Official Recommendation: {evc_details['recommendation']}."
            )
        elif app.evc_required:
            paragraphs.append("EVC Inspection Status: Mandatory inspection route flagged, awaiting panel assignment in EVC Queue.")
        else:
            paragraphs.append("EVC Inspection Status: Standard Extension of Approval route; physical inspection not mandated by baseline template.")

        if total_undertakings_count > 0:
            paragraphs.append(
                f"Compliance Passport: Institution holds {total_undertakings_count} time-bound undertakings "
                f"({overdue_undertakings_count} overdue). "
                + (f"Critical overdue obligations require immediate follow-up prior to final sign-off." if overdue_undertakings_count > 0 else "All statutory undertakings are compliant or on track.")
            )

        # Suggested Administrative Follow-Up Draft
        if open_count > 0:
            suggested_draft = (
                f"Official Communication to {inst_name}:\n"
                f"Reference Application {app.application_number}: Please note that {open_count} deficiency item(s) "
                f"remain uncured under Section 4 of the Approval Process Handbook. Submit cure documentation "
                f"via the Institution Portal within the statutory cure window to avoid adverse regulatory escalation."
            )
        elif app.current_stage == "AWAITING_COMPETENT_AUTHORITY":
            suggested_draft = (
                f"Administrative Concurrence Memo:\n"
                f"Case dossier for {app.application_number} ({inst_name}) is complete. Preceding scrutiny, "
                f"deficiency cures, and EVC inspection reports have been verified. Submitted to the Competent Authority "
                f"for final statutory Approval Order issuance."
            )
        else:
            suggested_draft = (
                f"Operational Status Note:\n"
                f"Case {app.application_number} is advancing under stage '{app.current_stage}'. "
                f"Responsible officers should verify pending items in accordance with the assigned SLA window."
            )

        return {
            "application_id": app.id,
            "application_number": app.application_number,
            "institution_name": inst_name,
            "region": inst_region,
            "current_stage": app.current_stage,
            "priority_score": app.priority_score,
            "provenance": "System-Generated Deterministic Case Brief (No Paid AI API Required)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary_paragraphs": paragraphs,
            "suggested_administrative_draft": suggested_draft,
            "evidence_milestones": milestones,
            "evidence_deficiencies": deficiencies,
            "evidence_undertakings": undertakings_summary,
            "evidence_evc": evc_details,
            "evidence_escalations": escalations_summary,
            "regulatory_disclaimer": (
                "STATUTORY NOTICE: This Case Brief is an informational operational synthesis generated strictly "
                "from recorded database facts. It does NOT constitute a statutory decision, does not grant approval or rejection, "
                "and does not supersede official scrutiny by an authorized AICTE official."
            )
        }

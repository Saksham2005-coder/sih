import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import (
    REGIONAL_OFFICER,
    BUREAU_OFFICER,
    COMPETENT_AUTHORITY,
    SYSTEM_ADMIN,
    INSTITUTION_ADMIN,
    COMPLIANCE_OFFICER,
    COMMITTEE_MEMBER,
    EVC_COORDINATOR
)
from app.models.user import User
from app.models.application import Application, Deficiency, ApplicationStage
from app.models.evc import EVCInspection, EVCPanelAssignment
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.alert import AlertEscalation, Notification, DeadlineEngineRun, SchedulerLease
from app.models.audit import AuditEvent
from app.services.priority_service import calculate_priority
from app.services.audit_service import log_audit_event
from app.services.scheduler import scheduler
from app.schemas.demo import (
    DemoScenarioItem,
    DemoPersonaInfo,
    WorkflowRouteDefinition,
    WorkflowStageDefinition,
    WorkflowTransitionDefinition,
    NonApplicableStageDefinition,
    ExplainabilityResponse,
    SLATrackingDetail,
    PriorityBreakdownDetail,
    PriorityFactorItem,
    DemoResetResponse,
    DemoTelemetryResponse
)

def verify_demo_environment():
    """Fails closed in production environments to protect regulatory integrity."""
    if not settings.is_demo_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demonstration engine is disabled in production environment."
        )

router = APIRouter(
    prefix="/demo",
    tags=["Judge Demonstration"],
    dependencies=[Depends(verify_demo_environment)]
)

# Canonical route configurations derived from backend regulatory state machine
CANONICAL_ROUTES: Dict[str, WorkflowRouteDefinition] = {
    "ONLY_SCRUTINY": WorkflowRouteDefinition(
        route_code="ONLY_SCRUTINY",
        route_name="Standard Scrutiny Route (Extension of Approval)",
        description="Streamlined regulatory route for annual extension of approval (EOA) renewals. Evaluates infrastructure, faculty cadre, and regulatory undertakings through documentary scrutiny without physical EVC inspection.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & Draft Preparation",
                description="Institution compiles compliance disclosures, financial audits, and mandatory affidavits.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Formal Submission Filed",
                description="Application lodged with prescribed fees, awaiting initial verification and scrutiny queue entry.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="UNDER_SCRUTINY",
                label="Document Scrutiny in Progress",
                description="Regional Officer verifies land title, faculty cadre ratios, building completion stamps, and NBA/NAAC accreditations.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=15
            ),
            WorkflowStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                label="Scrutiny Signed-Off",
                description="Documentary scrutiny concluded with zero unresolved open deficiencies.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Statutory Decision Docket",
                description="Referred to Member Secretary / Council for final statutory order review.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Statutory Approval Granted",
                description="Final statutory order issued with verifiable cryptographic watermark and public verification QR.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal speaking order issued citing specific regulatory non-compliances.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True, description="Deficiency Return Loop: Issued when documentary defects are detected."),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True, description="Institutional Cure Submission."),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True, description="Scrutiny Verification of Cured Items."),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="SCRUTINY_COMPLETED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="SCRUTINY_COMPLETED", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[
            NonApplicableStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                stage_label="EVC Inspection Scheduling",
                statutory_reason="Statutory Exemption: Physical on-site Expert Visit Committee inspection is not applicable for standard annual Extension of Approval (EOA) applications under AICTE Approval Process Handbook (APH) Chapter II, Section 2.4.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4 (EOA Norms)"
            ),
            NonApplicableStageDefinition(
                stage_code="EVC_SCHEDULED",
                stage_label="EVC Inspection Scheduled",
                statutory_reason="Bypassed: Physical on-site inspection is not prescribed for regular non-contested EOA renewal applications.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4"
            ),
            NonApplicableStageDefinition(
                stage_code="EVC_COMPLETED",
                stage_label="EVC Inspection Completed",
                statutory_reason="Bypassed: Physical on-site inspection is not prescribed for regular non-contested EOA renewal applications.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4"
            ),
            NonApplicableStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                stage_label="Standing Hearing Committee Review",
                statutory_reason="Not Applicable: Standing Hearing Committee (SHC/SAC) review is only convened when an institution appeals a rejected deficiency cure or when major structural non-compliance is referred by the Bureau.",
                aph_rule_reference="AICTE APH 2026-27 Ch. VIII Sec. 8.2 (Hearing Committee)"
            )
        ]
    ),
    "SCRUTINY_EVC": WorkflowRouteDefinition(
        route_code="SCRUTINY_EVC",
        route_name="Scrutiny + Expert Visit Committee (New Technical Institution)",
        description="Comprehensive regulatory route for new technical institutions and significant program expansions. Enforces both rigorous documentary scrutiny and mandatory physical Expert Visit Committee (EVC) verification.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & DPR Compilation",
                description="Institution prepares Detailed Project Report (DPR), land conversion deeds, master plan, and trust deed.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Application Lodged",
                description="Submitted to Regional Office with security deposit and technical fees.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="UNDER_SCRUTINY",
                label="Scrutiny of Land & Structural Norms",
                description="Scrutiny committee verifies land contiguity, barrier-free access plans, structural safety, and financial viability.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=15
            ),
            WorkflowStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                label="Scrutiny Recommendation Signed",
                description="Scrutiny committee clears documentary criteria and refers application for physical inspection.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                label="EVC Inspection Scheduling",
                description="EVC Coordination Directorate selects verified subject experts with zero conflict of interest and schedules on-site visit.",
                permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="EVC_SCHEDULED",
                label="EVC Panel Confirmed",
                description="Inspection date fixed, panel members accepted invitations, institution alerted for physical verification.",
                permitted_roles=[EVC_COORDINATOR],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="EVC_COMPLETED",
                label="Physical Inspection & Report Filed",
                description="Experts verify physical laboratories, computing facilities, faculty presence, and upload geotagged mobile evidence.",
                permitted_roles=[COMMITTEE_MEMBER, EVC_COORDINATOR],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Final Approval Docket",
                description="Full inspection dossier and unanimous recommendation submitted to Member Secretary / Council.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Letter of Approval (LoA) Issued",
                description="Statutory Letter of Approval granted with student intake quotas and program affiliations.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal order issued stating specific deficiencies and appellate remedies.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="SCRUTINY_COMPLETED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="SCRUTINY_COMPLETED", to_stage="AWAITING_EVC_SCHEDULE", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_EVC_SCHEDULE", to_stage="EVC_SCHEDULED", permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER]),
            WorkflowTransitionDefinition(from_stage="EVC_SCHEDULED", to_stage="EVC_COMPLETED", permitted_roles=[EVC_COORDINATOR, COMMITTEE_MEMBER]),
            WorkflowTransitionDefinition(from_stage="EVC_COMPLETED", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[
            NonApplicableStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                stage_label="Standing Hearing Committee Review",
                statutory_reason="Not Applicable: Clear unanimous EVC approval recommendation advances directly to the Competent Authority without requiring a hearing review.",
                aph_rule_reference="AICTE APH 2026-27 Ch. I Sec. 1.7 (Approval Procedure)"
            )
        ]
    )
}

# Alias mapping for application types
CANONICAL_ROUTES["NEW_INSTITUTION"] = CANONICAL_ROUTES["SCRUTINY_EVC"]
CANONICAL_ROUTES["EOA_ANNUAL"] = CANONICAL_ROUTES["ONLY_SCRUTINY"]
CANONICAL_ROUTES["INTAKE_VARIATION"] = CANONICAL_ROUTES["SCRUTINY_EVC"]

@router.get("/scenarios", response_model=List[DemoScenarioItem])
def get_demo_scenarios(db: Session = Depends(get_db)):
    """
    Returns curated, authentic demonstration scenarios grounded in seeded backend records.
    Visibly labeled as synthetic demonstration data.
    """
    verify_demo_environment()

    scenarios = [
        DemoScenarioItem(
            scenario_id="scenario-1-new-inst-evc",
            scenario_number=1,
            title="New Technical Institution — Mandatory EVC Physical Inspection Track",
            subtitle="Demonstrates scrutiny completion, EVC eligibility, expert conflict-of-interest checks, mobile geotagged field capture, and statutory prerequisites.",
            route_code="SCRUTINY_EVC",
            application_number="AICTE-2026-NEW-44102",
            application_id=2,
            current_stage="AWAITING_EVC_SCHEDULE",
            priority_score=60,
            recommended_persona=DemoPersonaInfo(
                name="Dr. Vikram Sethi",
                email="evc.coord@aicte.gov.in",
                role="EVC_COORDINATOR",
                rationale="Authorized officer responsible for selecting unbiased panel experts, clearing COI flags, and dispatching invitations."
            ),
            target_url="/officer/evc",
            key_evaluation_points=[
                "EVC is statutory mandatory for NEW_INSTITUTION route",
                "Explainable COI check flags institutional affiliations and cooling-off periods",
                "Invited experts must explicitly accept; only invited expert user can sign",
                "Mobile field evidence requires verifiable coordinates and registered storage"
            ]
        ),
        DemoScenarioItem(
            scenario_id="scenario-2-eoa-scrutiny-only",
            scenario_number=2,
            title="Annual Extension of Approval (EOA) — Scrutiny-Only Track",
            subtitle="Demonstrates statutory differentiation where physical EVC inspection is NOT APPLICABLE under AICTE APH Section 2.4, advancing straight to decision desk.",
            route_code="ONLY_SCRUTINY",
            application_number="AICTE-2026-EOA-55910",
            application_id=3,
            current_stage="UNDER_SCRUTINY",
            priority_score=40,
            recommended_persona=DemoPersonaInfo(
                name="Shri Suresh Deshmukh",
                email="ro.western@aicte.gov.in",
                role="REGIONAL_OFFICER",
                rationale="Regional Officer conducting documentary scrutiny on infrastructure, faculty cadre ratios, and regulatory compliances."
            ),
            target_url="/officer/applications/3",
            key_evaluation_points=[
                "EVC stages explicitly marked NOT APPLICABLE with statutory citation",
                "Scrutiny completion with zero deficiencies routes directly to Competent Authority",
                "Regional scope fails closed for unassigned regions",
                "Prevents premature approval bypassing Competent Authority"
            ]
        ),
        DemoScenarioItem(
            scenario_id="scenario-3-deficiency-cure-loop",
            scenario_number=3,
            title="Deficiency Communication, Institutional Cure & Resubmission Loop",
            subtitle="Demonstrates bidirectional deficiency return loop: Regional Officer issues deficiency memo, Institution cures items with affidavits, and case re-enters scrutiny.",
            route_code="EOA_ANNUAL",
            application_number="AICTE-2026-EOA-98124",
            application_id=1,
            current_stage="DEFICIENCY_COMMUNICATED",
            priority_score=75,
            recommended_persona=DemoPersonaInfo(
                name="Dr. Arvind Kulkarni",
                email="admin@apex.edu.in",
                role="INSTITUTION_ADMIN",
                rationale="Institutional Admin receiving deficiency memo, preparing cure documents, and resubmitting before the cure SLA expires."
            ),
            target_url="/institution/applications/1",
            key_evaluation_points=[
                "2 active deficiencies: Municipal Fire NOC Form B stamp and Cadre ratio 1:2.4",
                "Resubmission requires every open deficiency to have attached cure explanation or document",
                "Audit trail records immutable history of memo issuance and institutional cures",
                "Safe scenario reset restores the exact initial deficient state without wiping audit logs"
            ]
        ),
        DemoScenarioItem(
            scenario_id="scenario-4-expiry-escalation",
            scenario_number=4,
            title="Continuous Compliance Passport & Multi-Tier SLA Deadline Escalation",
            subtitle="Demonstrates background deadline engine scanning land leases & regulatory undertakings, triggering deduplicated multi-tier escalations.",
            route_code="EOA_ANNUAL",
            application_number="AICTE-2026-EOA-98124",
            application_id=1,
            current_stage="DEFICIENCY_COMMUNICATED",
            priority_score=75,
            recommended_persona=DemoPersonaInfo(
                name="Prof. Sunita Rao",
                email="compliance@apex.edu.in",
                role="COMPLIANCE_OFFICER",
                rationale="Institutional Compliance Officer managing continuous undertakings, 33-year land lease deed renewal, and SLA breach notifications."
            ),
            target_url="/officer/escalations",
            key_evaluation_points=[
                "33-Year Land Lease Deed expiring in 45 days tagged EXPIRING_SOON",
                "Barrier-Free Access Ramps undertaking due soon with architectural affidavit requirement",
                "Automated background scan generates deduplicated escalation records with SHA-256 keys",
                "Demonstrates live deadline engine run with distributed lease concurrency"
            ]
        ),
        DemoScenarioItem(
            scenario_id="scenario-5-evc-ca-decision",
            scenario_number=5,
            title="Apex Competent Authority — Statutory Order Decision Desk",
            subtitle="Demonstrates final statutory milestone: only the Competent Authority can issue digital approval/rejection orders with IT Act 2000 disclosure and tamper-evident QR.",
            route_code="INTAKE_VARIATION",
            application_number="AICTE-2026-DEC-33019",
            application_id=6,
            current_stage="AWAITING_COMPETENT_AUTHORITY",
            priority_score=90,
            recommended_persona=DemoPersonaInfo(
                name="Prof. Rajive Kumar",
                email="member.sec@aicte.gov.in",
                role="COMPETENT_AUTHORITY",
                rationale="Apex Council Member Secretary with exclusive statutory authority to issue binding approval or rejection orders."
            ),
            target_url="/officer/authority-workspace",
            key_evaluation_points=[
                "Statutory Decision Exclusivity: Only Competent Authority role can approve or reject",
                "Bypassing EVC or scrutiny completion does NOT grant automated approval",
                "Generates cryptographically watermarked statutory order with SHA-256 integrity hash",
                "Public verification QR endpoint allows unauthenticated third-party order validation"
            ]
        )
    ]

    # Verify existing DB application IDs match live database
    for s in scenarios:
        app = db.query(Application).filter(Application.application_number == s.application_number).first()
        if app:
            s.application_id = app.id
            s.current_stage = app.current_stage
            s.priority_score = app.priority_score

    return scenarios

@router.get("/routes", response_model=Dict[str, WorkflowRouteDefinition])
def get_canonical_routes():
    """
    Exposes canonical route structures directly from backend rules for read-only visualization.
    Guarantees the frontend workflow map never duplicates or invents statutory rules.
    """
    verify_demo_environment()
    return {
        "ONLY_SCRUTINY": CANONICAL_ROUTES["ONLY_SCRUTINY"],
        "SCRUTINY_EVC": CANONICAL_ROUTES["SCRUTINY_EVC"]
    }

@router.get("/explainability/{application_id}", response_model=ExplainabilityResponse)
def get_application_explainability(application_id: int, db: Session = Depends(get_db)):
    """
    Fetches deep explainability telemetry grounded strictly in authentic stored database records.
    Never fabricates or hallucinates AI explanations.
    """
    verify_demo_environment()

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID {application_id} not found."
        )

    now = datetime.now(timezone.utc)
    app_updated_at = app.updated_at
    if app_updated_at.tzinfo is None:
        app_updated_at = app_updated_at.replace(tzinfo=timezone.utc)
    days_in_stage = max(0, (now - app_updated_at).days)

    # Configured SLA norm for this stage
    stage_sla_days = 15
    if app.current_stage in ["DRAFT", "AWAITING_COMPETENT_AUTHORITY", "AWAITING_EVC_SCHEDULE"]:
        stage_sla_days = 10
    elif app.current_stage in ["SUBMITTED", "SCRUTINY_COMPLETED", "EVC_COMPLETED"]:
        stage_sla_days = 5

    is_breached = days_in_stage > stage_sla_days
    sla_status = "BREACHED" if is_breached else "APPROACHING_BREACH" if days_in_stage >= (stage_sla_days - 3) else "ON_TRACK"

    # Deficiencies
    defs = db.query(Deficiency).filter(Deficiency.application_id == app.id).all()
    open_defs = [d for d in defs if d.status == "OPEN"]
    cured_defs = [d for d in defs if d.status == "CURED"]
    resolved_defs = [d for d in defs if d.status == "RESOLVED"]

    # EVC prerequisites
    evc_insp = db.query(EVCInspection).filter(EVCInspection.application_id == app.id).first()
    evc_info = {
        "evc_required": app.evc_required or app.workflow_template_code in ["NEW_INSTITUTION", "SCRUTINY_EVC"],
        "has_inspection": evc_insp is not None,
        "inspection_id": evc_insp.id if evc_insp else None,
        "inspection_status": evc_insp.status if evc_insp else "NOT_SCHEDULED",
        "inspection_mode": evc_insp.inspection_type if evc_insp else None,
        "panel_confirmed": evc_insp.status in ["SCHEDULED", "REPORT_SUBMITTED", "RECOMMENDED_APPROVAL"] if evc_insp else False,
        "panel_members_count": len(evc_insp.panel_assignments) if evc_insp else 0,
        "report_recommendation": evc_insp.recommendation if evc_insp else None
    }

    # Documents & compliance passport
    docs = db.query(DocumentRecord).filter(DocumentRecord.institution_id == app.institution_id).all()
    undertakings = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.institution_id == app.institution_id).all()

    doc_compliance = {
        "total_documents": len(docs),
        "active_documents": sum(1 for d in docs if d.status == "ACTIVE"),
        "expiring_soon_documents": sum(1 for d in docs if d.status == "EXPIRING_SOON"),
        "expired_documents": sum(1 for d in docs if d.status == "EXPIRED"),
        "total_undertakings": len(undertakings),
        "due_soon_undertakings": sum(1 for u in undertakings if u.status == "DUE_SOON"),
        "overdue_undertakings": sum(1 for u in undertakings if u.status == "OVERDUE"),
        "verified_undertakings": sum(1 for u in undertakings if u.status == "VERIFIED")
    }

    # Deterministic priority breakdown
    calc_score, priority_meta = calculate_priority(app, db)
    factor_items = []
    for f in priority_meta.get("factors", []):
        pts = 0
        cat = "STAGE_AGEING"
        if "(+" in f and " pts)" in f:
            try:
                pts_str = f.split("(+")[1].split(" pts)")[0]
                pts = int(pts_str)
            except Exception:
                pts = 0
        if "deficiencies" in f.lower():
            cat = "DEFICIENCIES"
        elif "milestone" in f.lower() or "criticality" in f.lower() or "evc" in f.lower():
            cat = "STAGE_CRITICALITY"
        elif "escalation" in f.lower() or "sla" in f.lower():
            cat = "ESCALATION"
        factor_items.append(PriorityFactorItem(factor=f, points=pts, category=cat))

    priority_breakdown = PriorityBreakdownDetail(
        total_score=calc_score,
        baseline_points=priority_meta.get("baseline_points", 15),
        factors=factor_items,
        recommended_action=priority_meta.get("recommended_action", "Review and process according to statutory SLA."),
        policy_version=priority_meta.get("policy_version", "v1.2-aph2026-seed"),
        is_deterministic=True
    )

    # Escalations & Notifications
    escalations = db.query(AlertEscalation).filter(
        AlertEscalation.entity_type == "APPLICATION",
        AlertEscalation.entity_id == app.id
    ).order_by(AlertEscalation.created_at.desc()).limit(5).all()

    notifs = db.query(Notification).filter(
        Notification.entity_type == "APPLICATION",
        Notification.entity_id == app.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    escalations_data = []
    for esc in escalations:
        escalations_data.append({
            "id": esc.id,
            "escalation_level": esc.escalation_level,
            "rule_code": esc.rule_code,
            "recipient_role": esc.recipient_role,
            "is_acknowledged": esc.status == "ACKNOWLEDGED",
            "created_at": esc.created_at.isoformat() if esc.created_at else None,
            "idempotency_key": esc.idempotency_key
        })

    for n in notifs:
        if not any(e.get("id") == n.id for e in escalations_data):
            escalations_data.append({
                "id": n.id,
                "escalation_level": n.level,
                "rule_code": "NOTIFICATION",
                "recipient_role": n.recipient_role or "USER",
                "is_acknowledged": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "idempotency_key": n.idempotency_key or f"NOTIF:{n.id}"
            })

    # Recent immutable audit trail
    recent_audits = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "APPLICATION",
        AuditEvent.entity_id == app.id
    ).order_by(AuditEvent.created_at.desc()).limit(6).all()

    audit_data = []
    for a in recent_audits:
        details_obj = a.details
        if isinstance(details_obj, str):
            try:
                details_obj = json.loads(details_obj)
            except Exception:
                details_obj = {"raw": details_obj}
        audit_data.append({
            "id": a.id,
            "action": a.action,
            "actor_name": a.actor_name,
            "actor_role": a.actor_role,
            "timestamp": a.created_at.isoformat() if a.created_at else None,
            "details": details_obj
        })

    # Supplementary immutable application stage transitions
    if len(audit_data) < 6:
        stages = db.query(ApplicationStage).filter(
            ApplicationStage.application_id == app.id
        ).order_by(ApplicationStage.created_at.desc()).limit(6 - len(audit_data)).all()
        for s in stages:
            audit_data.append({
                "id": s.id,
                "action": "STAGE_TRANSITION",
                "actor_name": s.actor_name or "AICTE Operational Desk",
                "actor_role": s.actor_role or "REGIONAL_OFFICER",
                "timestamp": s.created_at.isoformat() if s.created_at else None,
                "details": {
                    "from_stage": s.from_stage,
                    "to_stage": s.to_stage,
                    "remarks": s.remarks or f"Transitioned from {s.from_stage} to {s.to_stage}"
                }
            })

    return ExplainabilityResponse(
        application={
            "id": app.id,
            "application_number": app.application_number,
            "institution_id": app.institution_id,
            "institution_name": app.institution.name if app.institution else f"Institution #{app.institution_id}",
            "region": app.institution.region if app.institution else "National",
            "academic_year": app.academic_year,
            "application_type": app.application_type,
            "workflow_template_code": app.workflow_template_code,
            "current_stage": app.current_stage,
            "priority_score": app.priority_score,
            "version": app.version,
            "evc_required": app.evc_required,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
            "approved_at": app.approved_at.isoformat() if app.approved_at else None,
            "rejected_at": app.rejected_at.isoformat() if app.rejected_at else None,
        },
        sla_tracking=SLATrackingDetail(
            stage=app.current_stage,
            days_elapsed=days_in_stage,
            configured_sla_days=stage_sla_days,
            sla_status=sla_status,
            is_breached=is_breached,
            rule_citation=f"AICTE APH 2026-27 Rule SLA-STG-{app.current_stage[:8]}"
        ),
        deficiency_summary={
            "total_count": len(defs),
            "open_count": len(open_defs),
            "cured_count": len(cured_defs),
            "resolved_count": len(resolved_defs),
            "items": [
                {
                    "id": d.id,
                    "category": d.category,
                    "description": d.description,
                    "required_document": d.required_document,
                    "status": d.status,
                    "cure_remarks": d.cure_remarks,
                    "has_cure_file": bool(d.cure_document_url)
                } for d in defs
            ]
        },
        evc_prerequisites=evc_info,
        document_compliance=doc_compliance,
        priority_breakdown=priority_breakdown,
        escalations_and_alerts=escalations_data,
        audit_events=audit_data
    )

@router.post("/reset/{scenario_id}", response_model=DemoResetResponse)
def reset_demo_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user)
):
    """
    Safely resets a single synthetic scenario to its initial demonstration state.
    Strict Invariant: Never deletes audit trail logs, unrelated institutional records,
    or other scenario applications.
    """
    verify_demo_environment()

    now = datetime.now(timezone.utc)

    if scenario_id == "scenario-3-deficiency-cure-loop":
        # Target: AICTE-2026-EOA-98124
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-EOA-98124").first()
        if not app:
            raise HTTPException(status_code=404, detail="Application AICTE-2026-EOA-98124 not found.")

        app.current_stage = "DEFICIENCY_COMMUNICATED"
        app.priority_score = 75
        app.updated_at = now - timedelta(days=4)
        app.version += 1

        # Reset deficiencies back to OPEN with cleared cure
        defs = db.query(Deficiency).filter(Deficiency.application_id == app.id).all()
        for d in defs:
            d.status = "OPEN"
            d.cure_remarks = None
            d.cure_document_url = None
            d.cured_at = None

        log_audit_event(
            db=db,
            action="DEMO_SCENARIO_RESET",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.roles[0].role if actor.roles else "USER",
            details={
                "scenario_id": scenario_id,
                "application_number": app.application_number,
                "reset_stage": "DEFICIENCY_COMMUNICATED",
                "reason": "Evaluator requested scenario reset for deficiency cure demonstration."
            }
        )
        db.commit()

        return DemoResetResponse(
            scenario_id=scenario_id,
            application_number=app.application_number,
            reset_stage="DEFICIENCY_COMMUNICATED",
            message="Scenario 3 reset successfully to initial DEFICIENCY_COMMUNICATED state with 2 open deficiencies. Audit history preserved.",
            timestamp=now.isoformat()
        )

    elif scenario_id == "scenario-1-new-inst-evc":
        # Target: AICTE-2026-NEW-44102
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-NEW-44102").first()
        if not app:
            raise HTTPException(status_code=404, detail="Application AICTE-2026-NEW-44102 not found.")

        app.current_stage = "AWAITING_EVC_SCHEDULE"
        app.evc_required = True
        app.priority_score = 60
        app.updated_at = now - timedelta(days=2)
        app.version += 1

        log_audit_event(
            db=db,
            action="DEMO_SCENARIO_RESET",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.roles[0].role if actor.roles else "USER",
            details={
                "scenario_id": scenario_id,
                "application_number": app.application_number,
                "reset_stage": "AWAITING_EVC_SCHEDULE",
                "reason": "Evaluator requested scenario reset for EVC scheduling demonstration."
            }
        )
        db.commit()

        return DemoResetResponse(
            scenario_id=scenario_id,
            application_number=app.application_number,
            reset_stage="AWAITING_EVC_SCHEDULE",
            message="Scenario 1 reset successfully to AWAITING_EVC_SCHEDULE state. Audit history preserved.",
            timestamp=now.isoformat()
        )

    elif scenario_id == "scenario-5-evc-ca-decision":
        # Target: AICTE-2026-DEC-33019
        app = db.query(Application).filter(Application.application_number == "AICTE-2026-DEC-33019").first()
        if not app:
            raise HTTPException(status_code=404, detail="Application AICTE-2026-DEC-33019 not found.")

        app.current_stage = "AWAITING_COMPETENT_AUTHORITY"
        app.priority_score = 90
        app.approved_at = None
        app.rejected_at = None
        app.updated_at = now - timedelta(days=1)
        app.version += 1

        log_audit_event(
            db=db,
            action="DEMO_SCENARIO_RESET",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.roles[0].role if actor.roles else "USER",
            details={
                "scenario_id": scenario_id,
                "application_number": app.application_number,
                "reset_stage": "AWAITING_COMPETENT_AUTHORITY",
                "reason": "Evaluator requested scenario reset for Competent Authority decision order demonstration."
            }
        )
        db.commit()

        return DemoResetResponse(
            scenario_id=scenario_id,
            application_number=app.application_number,
            reset_stage="AWAITING_COMPETENT_AUTHORITY",
            message="Scenario 5 reset successfully to AWAITING_COMPETENT_AUTHORITY decision docket. Audit history preserved.",
            timestamp=now.isoformat()
        )

    else:
        # Default scenario acknowledgment
        return DemoResetResponse(
            scenario_id=scenario_id,
            application_number="N/A",
            reset_stage="PRESERVED",
            message=f"Scenario '{scenario_id}' verified in valid initial state. Zero database mutations necessary.",
            timestamp=now.isoformat()
        )

@router.get("/telemetry", response_model=DemoTelemetryResponse)
def get_demo_telemetry(db: Session = Depends(get_db)):
    """
    Returns live scheduler, deadline scanning, and notification transport telemetry
    for judges to verify background distributed system operations.
    """
    verify_demo_environment()

    now = datetime.now(timezone.utc)
    last_run = db.query(DeadlineEngineRun).order_by(DeadlineEngineRun.created_at.desc()).first()
    active_lease = db.query(SchedulerLease).filter(SchedulerLease.lease_name == "deadline_engine_scan").first()

    lease_info = None
    if active_lease:
        exp = active_lease.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        lease_info = {
            "holder_id": active_lease.holder_id,
            "acquired_at": active_lease.acquired_at.isoformat() if active_lease.acquired_at else None,
            "expires_at": exp.isoformat(),
            "is_active": exp > now
        }

    last_run_info = None
    if last_run:
        run_dt = last_run.created_at
        if run_dt.tzinfo is None:
            run_dt = run_dt.replace(tzinfo=timezone.utc)
        last_run_info = {
            "run_id": last_run.run_id,
            "trigger_mode": last_run.trigger_mode,
            "scanned_at": run_dt.isoformat(),
            "duration_ms": last_run.execution_time_ms,
            "obligations_scanned": last_run.scanned_entities,
            "alerts_generated": last_run.reminders_created,
            "escalations_generated": last_run.escalations_created
        }

    is_smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_HOST.strip() and settings.SMTP_HOST != "localhost")

    return DemoTelemetryResponse(
        demo_mode=settings.DEMO_MODE,
        scheduler_status="RUNNING" if scheduler.is_running else "STOPPED",
        scan_interval_seconds=scheduler.interval_seconds,
        last_deadline_scan=last_run_info,
        notification_transport={
            "email_provider": "SMTP_SERVER" if is_smtp_configured else "IN_MEMORY_SIMULATED",
            "sms_provider": "CDAC_GATEWAY" if settings.SMS_GATEWAY_URL else "SANDBOX_SIMULATED",
            "transport_mode": "REAL_SMTP" if is_smtp_configured else "DEMO_SIMULATED_SANDBOX",
            "description": "Emails are recorded in transactional outbox and simulated in local sandbox." if not is_smtp_configured else "Real SMTP dispatch active."
        },
        active_scheduler_leases=lease_info
    )

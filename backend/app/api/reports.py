import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.alert import AlertEscalation
from app.models.audit import AuditEvent
from app.models.evc import EVCInspection
from app.models.institution import Institution
from app.models.rule import RuleDefinition
from app.schemas.report import (
    OperationalSummaryResponse, CommandCentreResponse,
    PriorityActionItem, RecentActivityItem, SlaAdherenceResponse,
    EvcAnalyticsResponse, ComplianceAnalyticsResponse,
    DocumentAnalyticsResponse, EscalationsAnalyticsResponse,
    RegionalPerformanceItem, RegionalPerformanceResponse
)
from app.services.priority_service import calculate_priority
from app.services.compliance_service import ComplianceService
from app.services.evc_service import EVCService
from app.services.audit_service import log_audit_event
from app.api.audit import sanitize_csv_cell

router = APIRouter(prefix="/reports", tags=["Reports & Command Center"])


def get_scoped_queries(db: Session, current_user: User, region: Optional[str] = None):
    """Derives properly scoped queries for applications, undertakings, documents and EVC."""
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    app_q = db.query(Application).join(Institution, Application.institution_id == Institution.id)
    u_q = db.query(ComplianceUndertaking).join(Institution, ComplianceUndertaking.institution_id == Institution.id)
    doc_q = db.query(DocumentRecord).join(Institution, DocumentRecord.institution_id == Institution.id)
    evc_q = db.query(EVCInspection).join(Application, EVCInspection.application_id == Application.id).join(Institution, Application.institution_id == Institution.id)

    if not is_officer and current_user.institution_id:
        app_q = app_q.filter(Application.institution_id == current_user.institution_id)
        u_q = u_q.filter(ComplianceUndertaking.institution_id == current_user.institution_id)
        doc_q = doc_q.filter(DocumentRecord.institution_id == current_user.institution_id)
        evc_q = evc_q.filter(Application.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        app_q = app_q.filter(Institution.region == current_user.region)
        u_q = u_q.filter(Institution.region == current_user.region)
        doc_q = doc_q.filter(Institution.region == current_user.region)
        evc_q = evc_q.filter(Institution.region == current_user.region)
    elif "EVC_COORDINATOR" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if current_user.region:
            app_q = app_q.filter(Institution.region == current_user.region)
            evc_q = evc_q.filter(Institution.region == current_user.region)
        app_q = app_q.filter(or_(
            Application.evc_required == True,
            Application.current_stage.in_(["AWAITING_EVC_SCHEDULE", "EVC_SCHEDULED", "EVC_COMPLETED"]),
            Application.workflow_template_code.in_(["NEW_INSTITUTION", "SCRUTINY_EVC", "EVC_SAC_SHC", "ONLY_EVC"])
        ))
    elif "COMMITTEE_MEMBER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        assigned_evc_app_ids = db.query(EVCInspection.application_id).filter(
            or_(
                EVCInspection.convener_user_id == current_user.id,
                EVCInspection.expert_user_id == current_user.id,
                EVCInspection.completed_by_id == current_user.id
            )
        )
        app_q = app_q.filter(or_(
            Application.current_stage == "AWAITING_SAC_CAC_REVIEW",
            Application.id.in_(assigned_evc_app_ids)
        ))
        evc_q = evc_q.filter(or_(
            EVCInspection.convener_user_id == current_user.id,
            EVCInspection.expert_user_id == current_user.id,
            EVCInspection.completed_by_id == current_user.id,
            EVCInspection.status.in_(["SCHEDULED", "REPORT_SUBMITTED", "IN_PROGRESS"])
        ))
    else:
        # National officer or unassigned
        if region:
            app_q = app_q.filter(Institution.region == region)
            u_q = u_q.filter(Institution.region == region)
            doc_q = doc_q.filter(Institution.region == region)
            evc_q = evc_q.filter(Institution.region == region)

    return app_q, u_q, doc_q, evc_q


@router.get("/summary", response_model=OperationalSummaryResponse)
def get_operational_summary(
    region: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
        "BUREAU_OFFICER", "COMMITTEE_MEMBER", "EVC_COORDINATOR",
        "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Reconciled operational summary counts across all modules with optional regional and date-range filters."""
    app_q, u_q, doc_q, evc_q = get_scoped_queries(db, current_user, region=region)

    if date_from:
        app_q = app_q.filter(Application.created_at >= date_from)
        u_q = u_q.filter(ComplianceUndertaking.created_at >= date_from)
        doc_q = doc_q.filter(DocumentRecord.created_at >= date_from)
    if date_to:
        app_q = app_q.filter(Application.created_at <= date_to)
        u_q = u_q.filter(ComplianceUndertaking.created_at <= date_to)
        doc_q = doc_q.filter(DocumentRecord.created_at <= date_to)

    total_apps = app_q.count()
    pending_scrutiny = app_q.filter(Application.current_stage.in_(["SUBMITTED", "UNDER_SCRUTINY", "RESUBMITTED"])).count()
    deficiency_cure = app_q.filter(Application.current_stage == "DEFICIENCY_COMMUNICATED").count()
    awaiting_evc = app_q.filter(Application.current_stage == "AWAITING_EVC_SCHEDULE").count()
    evc_scheduled = app_q.filter(Application.current_stage == "EVC_SCHEDULED").count()
    approved = app_q.filter(Application.current_stage == "APPROVED").count()
    rejected = app_q.filter(Application.current_stage == "REJECTED").count()

    total_u = u_q.count()
    overdue_u = u_q.filter(ComplianceUndertaking.status == "OVERDUE").count()
    expiring_docs = doc_q.filter(DocumentRecord.status.in_(["EXPIRING_SOON", "EXPIRED"])).count()
    
    # Active escalations
    esc_q = db.query(AlertEscalation).filter(AlertEscalation.status == "ACTIVE")
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        esc_q = esc_q.filter(or_(AlertEscalation.region == current_user.region, AlertEscalation.region == None))
    elif not any(r in ["REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"] for r in user_roles):
        if current_user.institution_id:
            esc_q = esc_q.filter(AlertEscalation.institution_id == current_user.institution_id)
    elif region:
        esc_q = esc_q.filter(AlertEscalation.region == region)

    if date_from:
        esc_q = esc_q.filter(AlertEscalation.created_at >= date_from)
    if date_to:
        esc_q = esc_q.filter(AlertEscalation.created_at <= date_to)

    active_esc = esc_q.count()

    # Stage breakdown
    stage_counts = app_q.with_entities(Application.current_stage, func.count(Application.id)).group_by(Application.current_stage).all()
    stage_dict = {s: c for s, c in stage_counts}

    # Regional breakdown
    reg_counts = app_q.with_entities(Institution.region, func.count(Application.id)).group_by(Institution.region).all()
    reg_dict = {r: c for r, c in reg_counts}

    return OperationalSummaryResponse(
        total_applications=total_apps,
        pending_scrutiny=pending_scrutiny,
        deficiency_cure_required=deficiency_cure,
        awaiting_evc=awaiting_evc,
        evc_scheduled=evc_scheduled,
        approved=approved,
        rejected=rejected,
        total_undertakings=total_u,
        overdue_undertakings=overdue_u,
        expiring_documents=expiring_docs,
        active_escalations=active_esc,
        stage_breakdown=stage_dict,
        regional_breakdown=reg_dict,
        filtered_region=region
    )


@router.get("/command-centre", response_model=CommandCentreResponse)
def get_command_centre(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
        "BUREAU_OFFICER", "COMMITTEE_MEMBER", "EVC_COORDINATOR",
        "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Full operational Command Centre dossier with bottlenecks, priority queue, and recent audit activity."""
    summary = get_operational_summary(db=db, current_user=current_user)
    app_q, u_q, doc_q, evc_q = get_scoped_queries(db, current_user)
    now = datetime.now(timezone.utc)

    # 1. Bottleneck Analytics
    # Repeated returns: applications with > 1 return to DEFICIENCY_COMMUNICATED
    repeated_returns_count = db.query(ApplicationStage.application_id).filter(
        ApplicationStage.to_stage == "DEFICIENCY_COMMUNICATED"
    ).group_by(ApplicationStage.application_id).having(func.count(ApplicationStage.id) > 1).count()

    # Verification backlogs
    backlog_undertakings = u_q.filter(ComplianceUndertaking.status == "PENDING_VERIFICATION").count()
    backlog_documents = doc_q.filter(DocumentRecord.status == "RENEWAL_SUBMITTED").count()
    unscheduled_evc = evc_q.filter(EVCInspection.status == "PENDING_ASSIGNMENT").count()

    # Average stage pendency
    active_apps = app_q.filter(~Application.current_stage.in_(["APPROVED", "REJECTED", "CLOSED"])).all()
    total_days = 0
    for a in active_apps:
        up = a.updated_at.replace(tzinfo=timezone.utc) if a.updated_at.tzinfo is None else a.updated_at
        total_days += max(0, (now - up).days)
    avg_ageing = round(total_days / len(active_apps), 1) if active_apps else 0.0

    bottlenecks = {
        "repeated_returns_count": repeated_returns_count,
        "verification_backlog_undertakings": backlog_undertakings,
        "verification_backlog_documents": backlog_documents,
        "unscheduled_evc_count": unscheduled_evc,
        "average_stage_ageing_days": avg_ageing
    }

    # 2. Priority Action Queue
    priority_items: List[PriorityActionItem] = []
    # Fetch active cases and rank deterministically
    candidates = app_q.filter(~Application.current_stage.in_(["APPROVED", "REJECTED", "CLOSED"])).all()
    scored_candidates = []
    for a in candidates:
        score, pdata = calculate_priority(a, db)
        up = a.updated_at.replace(tzinfo=timezone.utc) if a.updated_at.tzinfo is None else a.updated_at
        days_in_stg = max(0, (now - up).days)
        open_defs = db.query(Deficiency).filter(Deficiency.application_id == a.id, Deficiency.status == "OPEN").count()
        scored_candidates.append({
            "app": a,
            "score": score,
            "tier": pdata["tier"],
            "factors": pdata["factors"],
            "recommended_action": pdata["recommended_action"],
            "days_in_stage": days_in_stg,
            "open_deficiencies": open_defs
        })

    # Sort deterministically: score DESC, days_in_stage DESC, id ASC
    scored_candidates.sort(key=lambda x: (x["score"], x["days_in_stage"], -x["app"].id), reverse=True)

    for item in scored_candidates[:10]:
        a = item["app"]
        priority_items.append(PriorityActionItem(
            application_id=a.id,
            application_number=a.application_number,
            institution_name=a.institution.name,
            region=a.institution.region,
            current_stage=a.current_stage,
            priority_score=item["score"],
            priority_tier=item["tier"],
            priority_factors=item["factors"],
            days_in_stage=item["days_in_stage"],
            open_deficiencies_count=item["open_deficiencies"],
            recommended_action=item["recommended_action"],
            action_link=f"/officer/applications/{a.id}" if any(r.role != "INSTITUTION_ADMIN" for r in current_user.roles) else f"/institution/applications/{a.id}"
        ))

    # 3. Recent Activity Stream
    audit_q = db.query(AuditEvent)
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        audit_q = audit_q.filter(or_(AuditEvent.region == current_user.region, AuditEvent.region == None))
    elif not any(r in ["REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"] for r in user_roles):
        if current_user.institution_id:
            audit_q = audit_q.filter(AuditEvent.institution_id == current_user.institution_id)
            
    recent_audits = audit_q.order_by(AuditEvent.created_at.desc()).limit(10).all()
    recent_activity = [
        RecentActivityItem(
            id=ev.id,
            action=ev.action,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            actor_name=ev.actor_name,
            actor_role=ev.actor_role,
            details=ev.details,
            created_at=ev.created_at
        )
        for ev in recent_audits
    ]

    active_role_str = current_user.roles[0].role if current_user.roles else "OFFICER"
    if active_role_str == "COMMITTEE_MEMBER":
        jurisdiction_str = "Standing Hearing Committee (SAC/CAC)"
    elif active_role_str == "EVC_COORDINATOR":
        jurisdiction_str = f"{current_user.region or 'Regional'} EVC Directorate"
    elif active_role_str == "COMPETENT_AUTHORITY":
        jurisdiction_str = "Apex Council Competent Authority"
    elif active_role_str == "SYSTEM_ADMIN":
        jurisdiction_str = "Platform System Administration"
    elif current_user.region:
        jurisdiction_str = f"{current_user.region} Region"
    else:
        jurisdiction_str = "National Apex Scope"

    return CommandCentreResponse(
        summary=summary,
        bottlenecks=bottlenecks,
        priority_queue=priority_items,
        recent_activity=recent_activity,
        role_scope=active_role_str,
        jurisdiction=jurisdiction_str
    )


@router.get("/sla-adherence", response_model=SlaAdherenceResponse)
def get_sla_adherence_report(
    region: Optional[str] = None,
    stage: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed SLA adherence and stage turnaround analytics with optional filtering."""
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        region = current_user.region

    app_q, _, _, _ = get_scoped_queries(db, current_user, region=region)
    if stage:
        app_q = app_q.filter(Application.current_stage == stage)
    if date_from:
        app_q = app_q.filter(Application.created_at >= date_from)
    if date_to:
        app_q = app_q.filter(Application.created_at <= date_to)

    apps = app_q.all()
    now = datetime.now(timezone.utc)

    total_cases = len(apps)
    within_sla = 0
    breached_sla = 0

    stage_ageing: Dict[str, List[int]] = {}

    for a in apps:
        up = a.updated_at.replace(tzinfo=timezone.utc) if a.updated_at.tzinfo is None else a.updated_at
        days = max(0, (now - up).days)
        stage_ageing.setdefault(a.current_stage, []).append(days)

        # Baseline illustrative SLA of 14 days per stage
        if days > 14 and a.current_stage not in ("APPROVED", "REJECTED", "CLOSED"):
            breached_sla += 1
        else:
            within_sla += 1

    stage_breakdown = []
    for stg, days_list in stage_ageing.items():
        avg_d = round(sum(days_list) / len(days_list), 1) if days_list else 0.0
        breached_in_stg = sum(1 for d in days_list if d > 14)
        stage_breakdown.append({
            "stage": stg,
            "case_count": len(days_list),
            "average_days": avg_d,
            "breached_count": breached_in_stg,
            "within_count": len(days_list) - breached_in_stg
        })

    within_pct = round((within_sla / total_cases) * 100, 1) if total_cases else 100.0
    breached_pct = round((breached_sla / total_cases) * 100, 1) if total_cases else 0.0

    return SlaAdherenceResponse(
        total_cases_analyzed=total_cases,
        within_sla_count=within_sla,
        within_sla_percentage=within_pct,
        breached_sla_count=breached_sla,
        breached_sla_percentage=breached_pct,
        stage_sla_breakdown=stage_breakdown,
        filtered_region=region,
        filtered_stage=stage
    )


@router.get("/evc-analytics", response_model=EvcAnalyticsResponse)
def get_evc_analytics_report(
    region: Optional[str] = None,
    inspection_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed EVC inspection queues, panel assignments, eligibility, and recommendation distributions."""
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        region = current_user.region

    app_q, _, _, evc_q = get_scoped_queries(db, current_user, region=region)
    if inspection_type:
        evc_q = evc_q.filter(EVCInspection.inspection_type == inspection_type)
    if date_from:
        evc_q = evc_q.filter(EVCInspection.created_at >= date_from)
    if date_to:
        evc_q = evc_q.filter(EVCInspection.created_at <= date_to)

    inspections = evc_q.all()

    # Calculate eligible applications
    apps = app_q.all()
    eligible_count = sum(1 for a in apps if EVCService.is_evc_eligible(a))

    total = len(inspections)
    scheduled = sum(1 for i in inspections if i.status in ("SCHEDULED", "IN_PROGRESS"))
    completed = sum(1 for i in inspections if i.status in ("REPORT_SUBMITTED", "RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"))

    recs: Dict[str, int] = {}
    types: Dict[str, int] = {}

    for i in inspections:
        if i.recommendation:
            recs[i.recommendation] = recs.get(i.recommendation, 0) + 1
        if i.inspection_type:
            types[i.inspection_type] = types.get(i.inspection_type, 0) + 1

    return EvcAnalyticsResponse(
        total_inspections=total,
        eligible_count=eligible_count,
        scheduled_count=scheduled,
        completed_count=completed,
        recommendations=recs,
        inspection_types=types,
        filtered_region=region
    )


@router.get("/compliance-analytics", response_model=ComplianceAnalyticsResponse)
def get_compliance_analytics_report(
    region: Optional[str] = None,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
        "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed compliance undertakings, verification progress, and correction tracking."""
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        region = current_user.region

    _, u_q, _, _ = get_scoped_queries(db, current_user, region=region)
    if status_filter:
        u_q = u_q.filter(ComplianceUndertaking.status == status_filter)
    if category:
        u_q = u_q.filter(ComplianceUndertaking.category == category)
    if date_from:
        u_q = u_q.filter(ComplianceUndertaking.created_at >= date_from)
    if date_to:
        u_q = u_q.filter(ComplianceUndertaking.created_at <= date_to)

    undertakings = u_q.all()
    total = len(undertakings)
    verified = sum(1 for u in undertakings if u.status == "VERIFIED")
    pending = sum(1 for u in undertakings if u.status == "PENDING_VERIFICATION")
    correction = sum(1 for u in undertakings if u.status == "CORRECTION_REQUIRED")
    overdue = sum(1 for u in undertakings if u.status == "OVERDUE" or ComplianceService.get_effective_status(u) == "OVERDUE")

    pct = round((verified / total) * 100, 1) if total else 100.0

    cats: Dict[str, int] = {}
    statuses: Dict[str, int] = {}
    for u in undertakings:
        cats[u.category] = cats.get(u.category, 0) + 1
        statuses[u.status] = statuses.get(u.status, 0) + 1

    return ComplianceAnalyticsResponse(
        total_undertakings=total,
        verified_count=verified,
        pending_verification_count=pending,
        correction_required_count=correction,
        overdue_count=overdue,
        compliance_percentage=pct,
        category_breakdown=cats,
        status_breakdown=statuses,
        filtered_region=region
    )


@router.get("/document-analytics", response_model=DocumentAnalyticsResponse)
def get_document_analytics_report(
    region: Optional[str] = None,
    status_filter: Optional[str] = None,
    document_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
        "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed lease deeds, fire safety NOCs, building approval validity, and renewal tracking."""
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        region = current_user.region

    _, _, doc_q, _ = get_scoped_queries(db, current_user, region=region)
    if status_filter:
        doc_q = doc_q.filter(DocumentRecord.status == status_filter)
    if document_type:
        doc_q = doc_q.filter(DocumentRecord.document_type == document_type)
    if date_from:
        doc_q = doc_q.filter(DocumentRecord.created_at >= date_from)
    if date_to:
        doc_q = doc_q.filter(DocumentRecord.created_at <= date_to)

    documents = doc_q.all()
    total = len(documents)
    active = sum(1 for d in documents if d.status in ("ACTIVE", "VERIFIED"))
    expiring = sum(1 for d in documents if d.status == "EXPIRING_SOON")
    renewal = sum(1 for d in documents if d.status == "RENEWAL_SUBMITTED")
    expired = sum(1 for d in documents if d.status == "EXPIRED")

    pct = round((active / total) * 100, 1) if total else 100.0

    types: Dict[str, int] = {}
    for d in documents:
        types[d.document_type] = types.get(d.document_type, 0) + 1

    return DocumentAnalyticsResponse(
        total_documents=total,
        active_count=active,
        expiring_soon_count=expiring,
        renewal_submitted_count=renewal,
        expired_count=expired,
        validity_compliance_percentage=pct,
        type_breakdown=types,
        filtered_region=region
    )


@router.get("/escalations-analytics", response_model=EscalationsAnalyticsResponse)
def get_escalations_analytics_report(
    region: Optional[str] = None,
    status_filter: Optional[str] = None,
    escalation_level: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed overdue matters and multi-tier alert escalation distribution."""
    user_roles = [r.role for r in current_user.roles]
    esc_q = db.query(AlertEscalation)

    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        esc_q = esc_q.filter(or_(AlertEscalation.region == current_user.region, AlertEscalation.region == None))
    elif region:
        esc_q = esc_q.filter(AlertEscalation.region == region)

    if status_filter:
        esc_q = esc_q.filter(AlertEscalation.status == status_filter)
    if escalation_level:
        esc_q = esc_q.filter(AlertEscalation.escalation_level == escalation_level)
    if date_from:
        esc_q = esc_q.filter(AlertEscalation.created_at >= date_from)
    if date_to:
        esc_q = esc_q.filter(AlertEscalation.created_at <= date_to)

    escalations = esc_q.all()
    total = len(escalations)
    active = sum(1 for e in escalations if e.status == "ACTIVE")
    acknowledged = sum(1 for e in escalations if e.status == "ACKNOWLEDGED")
    resolved = sum(1 for e in escalations if e.status == "RESOLVED")

    tiers: Dict[str, int] = {}
    triggers: Dict[str, int] = {}
    for e in escalations:
        tiers[e.escalation_level] = tiers.get(e.escalation_level, 0) + 1
        triggers[e.trigger_type] = triggers.get(e.trigger_type, 0) + 1

    return EscalationsAnalyticsResponse(
        total_escalations=total,
        active_count=active,
        acknowledged_count=acknowledged,
        resolved_count=resolved,
        tier_breakdown=tiers,
        trigger_breakdown=triggers,
        filtered_region=region
    )


@router.get("/regional-performance", response_model=RegionalPerformanceResponse)
def get_regional_performance_report(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Comparative region-wise processing performance, average turnaround, and workload distribution."""
    CANONICAL_REGIONS = ["Northern", "North-West", "Central", "Western", "South-West", "Southern", "Eastern"]
    user_roles = [r.role for r in current_user.roles]
    scoped_regions = [current_user.region] if ("REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles) else CANONICAL_REGIONS

    now = datetime.now(timezone.utc)
    items = []
    all_turnaround_days = []
    all_within_count = 0
    all_analyzed_count = 0

    for reg in scoped_regions:
        app_q = db.query(Application).join(Institution, Application.institution_id == Institution.id).filter(Institution.region == reg)
        if date_from:
            app_q = app_q.filter(Application.created_at >= date_from)
        if date_to:
            app_q = app_q.filter(Application.created_at <= date_to)

        apps = app_q.all()
        total_apps = len(apps)
        pending = sum(1 for a in apps if a.current_stage in ("SUBMITTED", "UNDER_SCRUTINY", "RESUBMITTED", "DEFICIENCY_COMMUNICATED"))
        in_evc = sum(1 for a in apps if a.current_stage in ("AWAITING_EVC_SCHEDULE", "EVC_SCHEDULED", "EVC_COMPLETED"))
        approved = sum(1 for a in apps if a.current_stage == "APPROVED")
        rejected = sum(1 for a in apps if a.current_stage == "REJECTED")

        days_list = []
        within_sla = 0
        for a in apps:
            up = a.updated_at.replace(tzinfo=timezone.utc) if a.updated_at.tzinfo is None else a.updated_at
            d = max(0, (now - up).days)
            days_list.append(d)
            if d <= 14 or a.current_stage in ("APPROVED", "REJECTED", "CLOSED"):
                within_sla += 1

        avg_days = round(sum(days_list) / len(days_list), 1) if days_list else 0.0
        sla_rate = round((within_sla / total_apps) * 100, 1) if total_apps else 100.0

        all_turnaround_days.extend(days_list)
        all_within_count += within_sla
        all_analyzed_count += total_apps

        esc_count = db.query(AlertEscalation).filter(AlertEscalation.region == reg, AlertEscalation.status == "ACTIVE").count()

        items.append(RegionalPerformanceItem(
            region=reg,
            total_applications=total_apps,
            pending_scrutiny=pending,
            in_evc=in_evc,
            approved=approved,
            rejected=rejected,
            avg_turnaround_days=avg_days,
            sla_compliance_rate=sla_rate,
            active_escalations=esc_count
        ))

    nat_avg = round(sum(all_turnaround_days) / len(all_turnaround_days), 1) if all_turnaround_days else 0.0
    nat_rate = round((all_within_count / all_analyzed_count) * 100, 1) if all_analyzed_count else 100.0

    return RegionalPerformanceResponse(
        regions=items,
        national_avg_turnaround_days=nat_avg,
        national_sla_compliance_rate=nat_rate
    )


@router.get("/export-csv")
def export_report_csv(
    report_type: str = Query("SUMMARY", pattern="^(SUMMARY|SLA|EVC|COMPLIANCE|DOCUMENTS|ESCALATIONS|REGIONAL)$"),
    region: Optional[str] = None,
    stage: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Generates sanitized, formula-injection safe CSV for any regulatory reporting category."""
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        region = current_user.region

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "SUMMARY":
        summary = get_operational_summary(region=region, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Metric", "Reconciled Value", "Scope"])
        writer.writerow(["Total Applications", sanitize_csv_cell(summary.total_applications), sanitize_csv_cell(region or "National")])
        writer.writerow(["Pending Scrutiny", sanitize_csv_cell(summary.pending_scrutiny), sanitize_csv_cell(region or "National")])
        writer.writerow(["Deficiency Cure Required", sanitize_csv_cell(summary.deficiency_cure_required), sanitize_csv_cell(region or "National")])
        writer.writerow(["Awaiting EVC Schedule", sanitize_csv_cell(summary.awaiting_evc), sanitize_csv_cell(region or "National")])
        writer.writerow(["EVC Scheduled", sanitize_csv_cell(summary.evc_scheduled), sanitize_csv_cell(region or "National")])
        writer.writerow(["Statutory Approvals", sanitize_csv_cell(summary.approved), sanitize_csv_cell(region or "National")])
        writer.writerow(["Rejections", sanitize_csv_cell(summary.rejected), sanitize_csv_cell(region or "National")])
        writer.writerow(["Total Undertakings", sanitize_csv_cell(summary.total_undertakings), sanitize_csv_cell(region or "National")])
        writer.writerow(["Overdue Undertakings", sanitize_csv_cell(summary.overdue_undertakings), sanitize_csv_cell(region or "National")])
        writer.writerow(["Expiring Documents", sanitize_csv_cell(summary.expiring_documents), sanitize_csv_cell(region or "National")])
        writer.writerow(["Active Escalations", sanitize_csv_cell(summary.active_escalations), sanitize_csv_cell(region or "National")])

    elif report_type == "SLA":
        sla = get_sla_adherence_report(region=region, stage=stage, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Stage Name", "Case Count", "Average Days", "Within SLA", "Breached SLA"])
        for row in sla.stage_sla_breakdown:
            writer.writerow([
                sanitize_csv_cell(row["stage"]),
                sanitize_csv_cell(row["case_count"]),
                sanitize_csv_cell(row["average_days"]),
                sanitize_csv_cell(row["within_count"]),
                sanitize_csv_cell(row["breached_count"])
            ])

    elif report_type == "EVC":
        evc = get_evc_analytics_report(region=region, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Category", "Metric Name", "Count"])
        writer.writerow(["Overview", "Total Inspections", sanitize_csv_cell(evc.total_inspections)])
        writer.writerow(["Overview", "Eligible Applications", sanitize_csv_cell(evc.eligible_count)])
        writer.writerow(["Overview", "Scheduled Inspections", sanitize_csv_cell(evc.scheduled_count)])
        writer.writerow(["Overview", "Completed Inspections", sanitize_csv_cell(evc.completed_count)])
        for rec, cnt in evc.recommendations.items():
            writer.writerow(["Recommendation", sanitize_csv_cell(rec), sanitize_csv_cell(cnt)])
        for itype, cnt in evc.inspection_types.items():
            writer.writerow(["Inspection Type", sanitize_csv_cell(itype), sanitize_csv_cell(cnt)])

    elif report_type == "COMPLIANCE":
        comp = get_compliance_analytics_report(region=region, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Metric", "Count", "Percentage"])
        writer.writerow(["Total Undertakings", sanitize_csv_cell(comp.total_undertakings), "100%"])
        writer.writerow(["Verified Compliance", sanitize_csv_cell(comp.verified_count), sanitize_csv_cell(f"{comp.compliance_percentage}%")])
        writer.writerow(["Pending Verification", sanitize_csv_cell(comp.pending_verification_count), ""])
        writer.writerow(["Correction Required", sanitize_csv_cell(comp.correction_required_count), ""])
        writer.writerow(["Overdue Obligations", sanitize_csv_cell(comp.overdue_count), ""])
        writer.writerow([])
        writer.writerow(["Category", "Count"])
        for cat, cnt in comp.category_breakdown.items():
            writer.writerow([sanitize_csv_cell(cat), sanitize_csv_cell(cnt)])

    elif report_type == "DOCUMENTS":
        docs = get_document_analytics_report(region=region, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Metric", "Count", "Percentage"])
        writer.writerow(["Total Documents", sanitize_csv_cell(docs.total_documents), "100%"])
        writer.writerow(["Active & Valid", sanitize_csv_cell(docs.active_count), sanitize_csv_cell(f"{docs.validity_compliance_percentage}%")])
        writer.writerow(["Expiring Soon", sanitize_csv_cell(docs.expiring_soon_count), ""])
        writer.writerow(["Renewal Submitted", sanitize_csv_cell(docs.renewal_submitted_count), ""])
        writer.writerow(["Expired Validity", sanitize_csv_cell(docs.expired_count), ""])
        writer.writerow([])
        writer.writerow(["Document Type", "Count"])
        for dtype, cnt in docs.type_breakdown.items():
            writer.writerow([sanitize_csv_cell(dtype), sanitize_csv_cell(cnt)])

    elif report_type == "ESCALATIONS":
        esc = get_escalations_analytics_report(region=region, date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Metric", "Count"])
        writer.writerow(["Total Escalations", sanitize_csv_cell(esc.total_escalations)])
        writer.writerow(["Active Escalations", sanitize_csv_cell(esc.active_count)])
        writer.writerow(["Acknowledged Escalations", sanitize_csv_cell(esc.acknowledged_count)])
        writer.writerow(["Resolved Escalations", sanitize_csv_cell(esc.resolved_count)])
        writer.writerow([])
        writer.writerow(["Escalation Tier", "Count"])
        for tier, cnt in esc.tier_breakdown.items():
            writer.writerow([sanitize_csv_cell(tier), sanitize_csv_cell(cnt)])
        writer.writerow([])
        writer.writerow(["Trigger Type", "Count"])
        for trig, cnt in esc.trigger_breakdown.items():
            writer.writerow([sanitize_csv_cell(trig), sanitize_csv_cell(cnt)])

    elif report_type == "REGIONAL":
        reg_rep = get_regional_performance_report(date_from=date_from, date_to=date_to, db=db, current_user=current_user)
        writer.writerow(["Region", "Total Applications", "Pending Scrutiny", "In EVC", "Approved", "Rejected", "Avg Turnaround (Days)", "SLA Compliance %", "Active Escalations"])
        for r in reg_rep.regions:
            writer.writerow([
                sanitize_csv_cell(r.region),
                sanitize_csv_cell(r.total_applications),
                sanitize_csv_cell(r.pending_scrutiny),
                sanitize_csv_cell(r.in_evc),
                sanitize_csv_cell(r.approved),
                sanitize_csv_cell(r.rejected),
                sanitize_csv_cell(r.avg_turnaround_days),
                sanitize_csv_cell(f"{r.sla_compliance_rate}%"),
                sanitize_csv_cell(r.active_escalations)
            ])
        writer.writerow([])
        writer.writerow(["National Benchmark", "", "", "", "", "", sanitize_csv_cell(reg_rep.national_avg_turnaround_days), sanitize_csv_cell(f"{reg_rep.national_sla_compliance_rate}%"), ""])

    # Log export audit event
    log_audit_event(
        db=db,
        action="REGULATORY_REPORT_EXPORTED",
        entity_type="REPORT",
        entity_id=0,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.roles[0].role if current_user.roles else "OFFICER",
        details={"report_type": report_type, "region": region}
    )
    db.commit()

    output.seek(0)
    filename = f"reguflow_report_{report_type.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

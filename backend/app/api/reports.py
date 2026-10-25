from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
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
    EvcAnalyticsResponse
)
from app.services.priority_service import calculate_priority

router = APIRouter(prefix="/reports", tags=["Reports & Command Center"])


def get_scoped_queries(db: Session, current_user: User):
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

    return app_q, u_q, doc_q, evc_q


@router.get("/summary", response_model=OperationalSummaryResponse)
def get_operational_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
        "BUREAU_OFFICER", "COMMITTEE_MEMBER", "EVC_COORDINATOR",
        "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Reconciled operational summary counts across all modules."""
    app_q, u_q, doc_q, evc_q = get_scoped_queries(db, current_user)

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
        regional_breakdown=reg_dict
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
    jurisdiction_str = f"{current_user.region} Region" if current_user.region else "National Apex Scope"

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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed SLA adherence and stage turnaround analytics."""
    app_q, _, _, _ = get_scoped_queries(db, current_user)
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
        stage_sla_breakdown=stage_breakdown
    )


@router.get("/evc-analytics", response_model=EvcAnalyticsResponse)
def get_evc_analytics_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ]))
):
    """Detailed EVC inspection queues, panel assignments, and recommendation distributions."""
    _, _, _, evc_q = get_scoped_queries(db, current_user)
    inspections = evc_q.all()

    total = len(inspections)
    scheduled = sum(1 for i in inspections if i.status in ("SCHEDULED", "IN_PROGRESS"))
    completed = sum(1 for i in inspections if i.status in ("REPORT_SUBMITTED", "RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"))

    recs: Dict[str, int] = {}
    types: Dict[str, int] = {}

    for i in inspections:
        if i.recommendation:
            recs[i.recommendation] = recs.get(i.recommendation, 0) + 1
        types[i.inspection_type] = types.get(i.inspection_type, 0) + 1

    return EvcAnalyticsResponse(
        total_inspections=total,
        scheduled_count=scheduled,
        completed_count=completed,
        recommendations=recs,
        inspection_types=types
    )

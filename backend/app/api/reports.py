from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.alert import AlertEscalation
from app.models.institution import Institution
from app.schemas.report import OperationalSummaryResponse

router = APIRouter(prefix="/reports", tags=["Reports & Command Center"])

@router.get("/summary", response_model=OperationalSummaryResponse)
def get_operational_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    app_q = db.query(Application).join(Institution, Application.institution_id == Institution.id)
    u_q = db.query(ComplianceUndertaking).join(Institution, ComplianceUndertaking.institution_id == Institution.id)
    doc_q = db.query(DocumentRecord).join(Institution, DocumentRecord.institution_id == Institution.id)

    if not is_officer and current_user.institution_id:
        app_q = app_q.filter(Application.institution_id == current_user.institution_id)
        u_q = u_q.filter(ComplianceUndertaking.institution_id == current_user.institution_id)
        doc_q = doc_q.filter(DocumentRecord.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles:
        app_q = app_q.filter(Institution.region == current_user.region)
        u_q = u_q.filter(Institution.region == current_user.region)
        doc_q = doc_q.filter(Institution.region == current_user.region)

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
    active_esc = db.query(AlertEscalation).filter(AlertEscalation.status == "ACTIVE").count()

    # Stage breakdown
    stage_counts = db.query(Application.current_stage, func.count(Application.id)).group_by(Application.current_stage).all()
    stage_dict = {s: c for s, c in stage_counts}

    # Regional breakdown
    reg_counts = db.query(Institution.region, func.count(Application.id)).join(Application, Application.institution_id == Institution.id).group_by(Institution.region).all()
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

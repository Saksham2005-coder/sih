from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_regional_access
from app.models.user import User
from app.models.evc import EVCInspection
from app.models.application import Application
from app.models.institution import Institution
from app.schemas.evc import EVCScheduleRequest, EVCReportSubmitRequest, EVCInspectionResponse
from app.services.evc_service import EVCService
from app.core.rbac import check_regional_scope, has_permission, Permission

router = APIRouter(prefix="/evc", tags=["EVC Management"])

@router.get("/queue", response_model=List[EVCInspectionResponse])
def get_evc_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EVCInspection).join(
        Application, EVCInspection.application_id == Application.id
    ).join(
        Institution, Application.institution_id == Institution.id
    )

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(Institution.region == current_user.region)

    inspections = query.order_by(EVCInspection.scheduled_date.asc().nullslast()).all()
    results = []
    for insp in inspections:
        results.append(EVCInspectionResponse(
            id=insp.id,
            application_id=insp.application_id,
            application_number=insp.application.application_number if insp.application else None,
            institution_id=insp.application.institution_id if insp.application else None,
            institution_name=insp.application.institution.name if (insp.application and insp.application.institution) else None,
            region=insp.application.institution.region if (insp.application and insp.application.institution) else None,
            inspection_type=insp.inspection_type,
            scheduled_date=insp.scheduled_date,
            convener_name=insp.convener_name,
            expert_member_name=insp.expert_member_name,
            coordinator_id=insp.coordinator_id,
            status=insp.status,
            report_url=insp.report_url,
            report_notes=insp.report_notes,
            recommendation=insp.recommendation,
            completed_at=insp.completed_at,
            completed_by_id=insp.completed_by_id,
            created_at=insp.created_at,
            updated_at=insp.updated_at
        ))
    return results

@router.post("/schedule", response_model=EVCInspectionResponse)
@router.post("/inspections", response_model=EVCInspectionResponse)
def schedule_evc_inspection(
    request: EVCScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = EVCService.schedule_inspection(
        db=db,
        application_id=request.application_id,
        inspection_type=request.inspection_type,
        scheduled_date=request.scheduled_date,
        convener_name=request.convener_name,
        expert_member_name=request.expert_member_name,
        actor=current_user
    )

    app = inspection.application
    return EVCInspectionResponse(
        id=inspection.id,
        application_id=inspection.application_id,
        application_number=app.application_number if app else None,
        institution_id=app.institution_id if app else None,
        institution_name=app.institution.name if (app and app.institution) else None,
        region=app.institution.region if (app and app.institution) else None,
        inspection_type=inspection.inspection_type,
        scheduled_date=inspection.scheduled_date,
        convener_name=inspection.convener_name,
        expert_member_name=inspection.expert_member_name,
        coordinator_id=inspection.coordinator_id,
        status=inspection.status,
        report_url=inspection.report_url,
        report_notes=inspection.report_notes,
        recommendation=inspection.recommendation,
        completed_at=inspection.completed_at,
        completed_by_id=inspection.completed_by_id,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )

@router.post("/{id}/submit-report", response_model=EVCInspectionResponse)
@router.post("/inspections/{id}/report", response_model=EVCInspectionResponse)
def submit_evc_report(
    id: int,
    request: EVCReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = EVCService.submit_report(
        db=db,
        inspection_id=id,
        report_url=request.report_url,
        report_notes=request.report_notes,
        recommendation=request.recommendation,
        actor=current_user
    )

    app = inspection.application
    return EVCInspectionResponse(
        id=inspection.id,
        application_id=inspection.application_id,
        application_number=app.application_number if app else None,
        institution_id=app.institution_id if app else None,
        institution_name=app.institution.name if (app and app.institution) else None,
        region=app.institution.region if (app and app.institution) else None,
        inspection_type=inspection.inspection_type,
        scheduled_date=inspection.scheduled_date,
        convener_name=inspection.convener_name,
        expert_member_name=inspection.expert_member_name,
        coordinator_id=inspection.coordinator_id,
        status=inspection.status,
        report_url=inspection.report_url,
        report_notes=inspection.report_notes,
        recommendation=inspection.recommendation,
        completed_at=inspection.completed_at,
        completed_by_id=inspection.completed_by_id,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )

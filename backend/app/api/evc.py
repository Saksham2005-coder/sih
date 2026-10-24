from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.evc import EVCInspection
from app.models.application import Application
from app.models.institution import Institution
from app.schemas.evc import EVCScheduleRequest, EVCReportSubmitRequest, EVCInspectionResponse
from app.services.workflow_engine import execute_transition
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/evc", tags=["EVC Management"])

@router.get("/queue", response_model=List[EVCInspectionResponse])
def get_evc_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspections = db.query(EVCInspection).join(Application, EVCInspection.application_id == Application.id).join(Institution, Application.institution_id == Institution.id).all()
    results = []
    for insp in inspections:
        results.append(EVCInspectionResponse(
            id=insp.id,
            application_id=insp.application_id,
            application_number=insp.application.application_number,
            institution_id=insp.application.institution_id,
            institution_name=insp.application.institution.name,
            region=insp.application.institution.region,
            inspection_type=insp.inspection_type,
            scheduled_date=insp.scheduled_date,
            convener_name=insp.convener_name,
            expert_member_name=insp.expert_member_name,
            status=insp.status,
            report_url=insp.report_url,
            report_notes=insp.report_notes,
            recommendation=insp.recommendation,
            created_at=insp.created_at,
            updated_at=insp.updated_at
        ))
    return results

@router.post("/schedule", response_model=EVCInspectionResponse)
def schedule_evc_inspection(
    request: EVCScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["EVC_COORDINATOR", "REGIONAL_OFFICER", "SYSTEM_ADMIN"]))
):
    app = db.query(Application).filter(Application.id == request.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    inspection = db.query(EVCInspection).filter(EVCInspection.application_id == app.id).first()
    if not inspection:
        inspection = EVCInspection(application_id=app.id)
        db.add(inspection)

    inspection.inspection_type = request.inspection_type
    inspection.scheduled_date = request.scheduled_date
    inspection.convener_name = request.convener_name
    inspection.expert_member_name = request.expert_member_name
    inspection.status = "SCHEDULED"

    # Automatically transition application to EVC_SCHEDULED if at AWAITING_EVC_SCHEDULE
    if app.current_stage == "AWAITING_EVC_SCHEDULE":
        execute_transition(
            db=db,
            application=app,
            to_stage="EVC_SCHEDULED",
            actor=current_user,
            remarks=f"EVC Inspection scheduled for {request.scheduled_date.strftime('%d %b %Y')} with Convener {request.convener_name}."
        )
    else:
        db.commit()

    db.refresh(inspection)

    log_audit_event(
        db=db,
        action="EVC_SCHEDULED",
        entity_type="EVC",
        entity_id=inspection.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="EVC_COORDINATOR",
        details={
            "application_id": app.id,
            "scheduled_date": request.scheduled_date.isoformat(),
            "convener": request.convener_name,
            "expert": request.expert_member_name
        }
    )

    return EVCInspectionResponse(
        id=inspection.id,
        application_id=inspection.application_id,
        application_number=app.application_number,
        institution_id=app.institution_id,
        institution_name=app.institution.name,
        region=app.institution.region,
        inspection_type=inspection.inspection_type,
        scheduled_date=inspection.scheduled_date,
        convener_name=inspection.convener_name,
        expert_member_name=inspection.expert_member_name,
        status=inspection.status,
        report_url=inspection.report_url,
        report_notes=inspection.report_notes,
        recommendation=inspection.recommendation,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )

@router.post("/{id}/submit-report", response_model=EVCInspectionResponse)
def submit_evc_report(
    id: int,
    request: EVCReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["EVC_COORDINATOR", "COMMITTEE_MEMBER", "REGIONAL_OFFICER", "SYSTEM_ADMIN"]))
):
    inspection = db.query(EVCInspection).filter(EVCInspection.id == id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="EVC Inspection not found")

    inspection.report_url = request.report_url
    inspection.report_notes = request.report_notes
    inspection.recommendation = request.recommendation
    inspection.status = "REPORT_SUBMITTED"

    app = inspection.application
    if app.current_stage == "EVC_SCHEDULED":
        execute_transition(
            db=db,
            application=app,
            to_stage="EVC_COMPLETED",
            actor=current_user,
            remarks=f"EVC Inspection report submitted. Committee Recommendation: {request.recommendation}."
        )
    else:
        db.commit()

    db.refresh(inspection)

    log_audit_event(
        db=db,
        action="EVC_REPORT_SUBMITTED",
        entity_type="EVC",
        entity_id=inspection.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="COMMITTEE_MEMBER",
        details={
            "application_id": app.id,
            "recommendation": request.recommendation,
            "notes": request.report_notes
        }
    )

    return EVCInspectionResponse(
        id=inspection.id,
        application_id=inspection.application_id,
        application_number=app.application_number,
        institution_id=app.institution_id,
        institution_name=app.institution.name,
        region=app.institution.region,
        inspection_type=inspection.inspection_type,
        scheduled_date=inspection.scheduled_date,
        convener_name=inspection.convener_name,
        expert_member_name=inspection.expert_member_name,
        status=inspection.status,
        report_url=inspection.report_url,
        report_notes=inspection.report_notes,
        recommendation=inspection.recommendation,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )

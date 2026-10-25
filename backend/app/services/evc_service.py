from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.evc import EVCInspection
from app.models.application import Application
from app.models.institution import Institution
from app.models.user import User
from app.models.alert import Notification
from app.services.workflow_engine import execute_transition
from app.services.audit_service import log_audit_event
from app.core.rbac import check_regional_scope, has_permission, Permission

VALID_RECOMMENDATIONS = {"RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"}

class EVCService:
    """
    Authoritative service governing Expert Visit Committee (EVC) scheduling, panel coordination,
    and inspection report lifecycle.
    """

    @staticmethod
    def is_evc_eligible(app: Application) -> bool:
        """Determines whether an application requires and is eligible for EVC inspection."""
        # EVC required for NEW_INSTITUTION, SCRUTINY_EVC, EVC_SAC_SHC, ONLY_EVC, or when explicitly flagged
        requires_evc = (
            app.workflow_template_code in ["NEW_INSTITUTION", "SCRUTINY_EVC", "EVC_SAC_SHC", "ONLY_EVC"]
            or app.evc_required
        )
        is_at_stage = app.current_stage in ["AWAITING_EVC_SCHEDULE", "EVC_SCHEDULED", "EVC_COMPLETED"]
        return requires_evc or is_at_stage

    @staticmethod
    def schedule_inspection(
        db: Session,
        application_id: int,
        inspection_type: str,
        scheduled_date: datetime,
        convener_name: str,
        expert_member_name: str,
        actor: User
    ) -> EVCInspection:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        # 1. Regional boundary check
        if app.institution:
            check_regional_scope(actor, app.institution.region)

        # 2. Permission check
        if not has_permission(actor, Permission.EVC_SCHEDULE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: User does not hold 'evc.schedule' permission."
            )

        # 3. Scheduled date validation (must be in future)
        now = datetime.now(timezone.utc)
        sched_utc = scheduled_date if scheduled_date.tzinfo else scheduled_date.replace(tzinfo=timezone.utc)
        if sched_utc <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled visit date must be set to a future date and time."
            )

        # 4. Panel composition validation
        if not convener_name or not convener_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Panel Convener name is required to form an EVC inspection panel."
            )
        if not expert_member_name or not expert_member_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject Expert Member name is required to form an EVC inspection panel."
            )

        # 5. Fetch or create EVC inspection record
        inspection = db.query(EVCInspection).filter(EVCInspection.application_id == app.id).first()
        if not inspection:
            inspection = EVCInspection(application_id=app.id)
            db.add(inspection)

        inspection.inspection_type = inspection_type
        inspection.scheduled_date = sched_utc
        inspection.convener_name = convener_name.strip()
        inspection.expert_member_name = expert_member_name.strip()
        inspection.coordinator_id = actor.id
        inspection.status = "SCHEDULED"

        # 6. Workflow transition to EVC_SCHEDULED if currently awaiting
        if app.current_stage == "AWAITING_EVC_SCHEDULE":
            execute_transition(
                db=db,
                application=app,
                to_stage="EVC_SCHEDULED",
                actor=actor,
                remarks=f"EVC Inspection panel scheduled for {sched_utc.strftime('%d %b %Y, %H:%M UTC')} with Convener {convener_name} and Expert {expert_member_name}."
            )
        else:
            db.commit()

        db.refresh(inspection)

        # 7. Audit log
        actor_role = actor.roles[0].role if actor.roles else "EVC_COORDINATOR"
        log_audit_event(
            db=db,
            action="EVC_PANEL_SCHEDULED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "application_number": app.application_number,
                "scheduled_date": sched_utc.isoformat(),
                "convener": convener_name,
                "expert": expert_member_name,
                "inspection_type": inspection_type
            }
        )

        return inspection

    @staticmethod
    def submit_report(
        db: Session,
        inspection_id: int,
        report_url: str,
        report_notes: str,
        recommendation: str,
        actor: User
    ) -> EVCInspection:
        inspection = db.query(EVCInspection).filter(EVCInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EVC inspection not found")

        # 1. Permission check
        if not has_permission(actor, Permission.EVC_REPORT):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: User does not hold 'evc.report' permission."
            )

        # 2. Recommendation validation
        if recommendation not in VALID_RECOMMENDATIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recommendation '{recommendation}'. Must be one of: {', '.join(sorted(VALID_RECOMMENDATIONS))}"
            )

        # 3. Report notes validation
        if not report_notes or not report_notes.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inspection report observations/notes are mandatory."
            )

        now = datetime.now(timezone.utc)
        inspection.report_url = report_url
        inspection.report_notes = report_notes.strip()
        inspection.recommendation = recommendation
        inspection.status = "REPORT_SUBMITTED"
        inspection.completed_at = now
        inspection.completed_by_id = actor.id

        # 4. Advance application to EVC_COMPLETED
        app = inspection.application
        if app.current_stage == "EVC_SCHEDULED":
            execute_transition(
                db=db,
                application=app,
                to_stage="EVC_COMPLETED",
                actor=actor,
                remarks=f"EVC Inspection report submitted. Committee Recommendation: {recommendation}. Notes: {report_notes[:100]}..."
            )
        else:
            db.commit()

        db.refresh(inspection)

        # 5. Audit log
        actor_role = actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER"
        log_audit_event(
            db=db,
            action="EVC_REPORT_SUBMITTED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "application_number": app.application_number,
                "recommendation": recommendation,
                "report_url": report_url
            }
        )

        return inspection

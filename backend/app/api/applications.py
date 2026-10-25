import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.institution import Institution
from app.schemas.application import (
    ApplicationResponse, ApplicationDetailResponse, ApplicationCreateRequest,
    ApplicationTransitionRequest, DeficiencyCreateRequest, DeficiencyCureRequest,
    DeficiencyResponse
)
from app.services.workflow_engine import execute_transition, get_allowed_transitions
from app.services.priority_service import calculate_priority
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    stage: Optional[str] = None,
    application_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).join(Institution, Application.institution_id == Institution.id)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    # Multi-tenant isolation: Institution users can only query their own records
    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        # Regional officer sees applications in their assigned region
        query = query.filter(Institution.region == current_user.region)

    if stage:
        query = query.filter(Application.current_stage == stage)
    if application_type:
        query = query.filter(Application.application_type == application_type)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Application.application_number.ilike(search_filter)) |
            (Institution.name.ilike(search_filter)) |
            (Institution.code.ilike(search_filter))
        )

    apps = query.order_by(Application.priority_score.desc(), Application.updated_at.desc()).all()
    
    results = []
    for app in apps:
        open_defs = db.query(Deficiency).filter(Deficiency.application_id == app.id, Deficiency.status == "OPEN").count()
        score, factors = calculate_priority(app, db)
        app.priority_score = score
        results.append(ApplicationResponse(
            id=app.id,
            application_number=app.application_number,
            institution_id=app.institution_id,
            institution_name=app.institution.name,
            region=app.institution.region,
            academic_year=app.academic_year,
            application_type=app.application_type,
            workflow_template_code=app.workflow_template_code,
            current_stage=app.current_stage,
            scrutiny_officer_id=app.scrutiny_officer_id,
            priority_score=score,
            priority_factors=factors,
            version=app.version,
            submitted_at=app.submitted_at,
            approved_at=app.approved_at,
            rejected_at=app.rejected_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
            open_deficiencies_count=open_defs
        ))
    return results

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    request: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN"]))
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="User is not associated with an institution.")

    # Generate sequential application number
    now = datetime.now(timezone.utc)
    count = db.query(Application).count() + 101
    app_num = f"AICTE-2026-EOA-{count:05d}"

    new_app = Application(
        application_number=app_num,
        institution_id=current_user.institution_id,
        academic_year=request.academic_year,
        application_type=request.application_type,
        workflow_template_code=request.application_type,
        current_stage="SUBMITTED",
        submitted_at=now,
        priority_score=30
    )
    db.add(new_app)
    db.flush()

    # Add initial stage timeline
    stage_event = ApplicationStage(
        application_id=new_app.id,
        from_stage="DRAFT",
        to_stage="SUBMITTED",
        actor_id=current_user.id,
        actor_role="INSTITUTION_ADMIN",
        actor_name=current_user.full_name,
        remarks="Regulatory application filed with prescribed fee and statutory undertakings."
    )
    db.add(stage_event)

    log_audit_event(
        db=db,
        action="APPLICATION_CREATED",
        entity_type="APPLICATION",
        entity_id=new_app.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="INSTITUTION_ADMIN",
        details={"application_number": app_num, "type": request.application_type}
    )

    db.commit()
    db.refresh(new_app)

    score, factors = calculate_priority(new_app, db)
    return ApplicationResponse(
        id=new_app.id,
        application_number=new_app.application_number,
        institution_id=new_app.institution_id,
        institution_name=new_app.institution.name,
        region=new_app.institution.region,
        academic_year=new_app.academic_year,
        application_type=new_app.application_type,
        workflow_template_code=new_app.workflow_template_code,
        current_stage=new_app.current_stage,
        scrutiny_officer_id=new_app.scrutiny_officer_id,
        priority_score=score,
        priority_factors=factors,
        version=new_app.version,
        submitted_at=new_app.submitted_at,
        created_at=new_app.created_at,
        updated_at=new_app.updated_at,
        open_deficiencies_count=0
    )

@router.get("/{id}", response_model=ApplicationDetailResponse)
def get_application_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Isolation check
    verify_institution_access(app.institution_id, current_user)

    score, factors = calculate_priority(app, db)
    open_defs = db.query(Deficiency).filter(Deficiency.application_id == app.id, Deficiency.status == "OPEN").count()

    return ApplicationDetailResponse(
        id=app.id,
        application_number=app.application_number,
        institution_id=app.institution_id,
        institution_name=app.institution.name,
        region=app.institution.region,
        academic_year=app.academic_year,
        application_type=app.application_type,
        workflow_template_code=app.workflow_template_code,
        current_stage=app.current_stage,
        scrutiny_officer_id=app.scrutiny_officer_id,
        priority_score=score,
        priority_factors=factors,
        version=app.version,
        submitted_at=app.submitted_at,
        approved_at=app.approved_at,
        rejected_at=app.rejected_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        open_deficiencies_count=open_defs,
        stages=app.stages,
        deficiencies=app.deficiencies
    )

@router.post("/{id}/transition", response_model=ApplicationDetailResponse)
def transition_application_stage(
    id: int,
    request: ApplicationTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)
    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    updated_app = execute_transition(
        db=db,
        application=app,
        to_stage=request.to_stage,
        actor=current_user,
        remarks=request.remarks,
        expected_version=request.expected_version
    )

    return get_application_detail(id=updated_app.id, db=db, current_user=current_user)

@router.post("/{id}/deficiencies", response_model=DeficiencyResponse, status_code=status.HTTP_201_CREATED)
def issue_deficiency(
    id: int,
    request: DeficiencyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    deficiency = Deficiency(
        application_id=app.id,
        category=request.category,
        description=request.description,
        required_document=request.required_document,
        status="OPEN"
    )
    db.add(deficiency)
    
    # Automatically move application to DEFICIENCY_COMMUNICATED if currently under scrutiny
    if app.current_stage == "UNDER_SCRUTINY":
        execute_transition(
            db=db,
            application=app,
            to_stage="DEFICIENCY_COMMUNICATED",
            actor=current_user,
            remarks=f"Deficiency issued in category '{request.category}': {request.description}"
        )
    else:
        db.commit()

    db.refresh(deficiency)
    return deficiency

@router.post("/{id}/cure-deficiency/{deficiency_id}", response_model=DeficiencyResponse)
def cure_deficiency(
    id: int,
    deficiency_id: int,
    request: DeficiencyCureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)

    deficiency = db.query(Deficiency).filter(
        Deficiency.id == deficiency_id,
        Deficiency.application_id == app.id
    ).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency item not found")

    deficiency.cure_remarks = request.cure_remarks
    if request.cure_document_url:
        deficiency.cure_document_url = request.cure_document_url
    deficiency.cured_at = datetime.now(timezone.utc)

    actor_role = current_user.roles[0].role if current_user.roles else "INSTITUTION_ADMIN"
    log_audit_event(
        db=db,
        action="DEFICIENCY_CURE_SUBMITTED",
        entity_type="DEFICIENCY",
        entity_id=deficiency.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"application_id": app.id, "remarks": request.cure_remarks}
    )

    db.commit()
    db.refresh(deficiency)
    return deficiency

@router.post("/{id}/resolve-deficiency/{deficiency_id}", response_model=DeficiencyResponse)
def resolve_deficiency(
    id: int,
    deficiency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.institution:
        verify_regional_access(app.institution.region, current_user)

    deficiency = db.query(Deficiency).filter(
        Deficiency.id == deficiency_id,
        Deficiency.application_id == app.id
    ).first()
    if not deficiency:
        raise HTTPException(status_code=404, detail="Deficiency item not found")

    deficiency.status = "CURED"
    deficiency.resolved_by_officer_id = current_user.id

    actor_role = current_user.roles[0].role if current_user.roles else "REGIONAL_OFFICER"
    log_audit_event(
        db=db,
        action="DEFICIENCY_RESOLVED",
        entity_type="DEFICIENCY",
        entity_id=deficiency.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"application_id": app.id, "deficiency_id": deficiency.id}
    )

    db.commit()
    db.refresh(deficiency)
    return deficiency

@router.get("/{id}/case-brief")
def get_case_brief(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deterministic Case Brief Assistant summarizing recorded application milestones and evidence"""
    from app.services.case_brief_service import CaseBriefService
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(app.institution_id, current_user)
    
    # Regional Officer access check
    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if app.institution.region != current_user.region:
            raise HTTPException(status_code=403, detail="Forbidden: Application outside assigned regional jurisdiction")

    return CaseBriefService.generate_case_brief(app.id, db)

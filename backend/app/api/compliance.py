from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.institution import Institution
from app.models.application import Application
from app.schemas.compliance import (
    ComplianceUndertakingResponse, ComplianceUndertakingCreate, ComplianceVerifyRequest, ComplianceEvidenceResponse
)
from app.services.compliance_service import ComplianceService
from app.services.audit_service import log_audit_event
from app.core.rbac import check_institution_scope, check_regional_scope, has_permission, Permission

router = APIRouter(prefix="/compliance", tags=["Compliance Passport"])

@router.get("/undertakings", response_model=List[ComplianceUndertakingResponse])
def list_undertakings(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ComplianceUndertaking).join(Institution, ComplianceUndertaking.institution_id == Institution.id)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(ComplianceUndertaking.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(Institution.region == current_user.region)

    if status_filter:
        query = query.filter(ComplianceUndertaking.status == status_filter)
    if category:
        query = query.filter(ComplianceUndertaking.category == category)
    if application_id:
        query = query.filter(ComplianceUndertaking.application_id == application_id)

    undertakings = query.order_by(ComplianceUndertaking.due_date.asc()).all()
    results = []
    for u in undertakings:
        eff_status = ComplianceService.get_effective_status(u)
        results.append(ComplianceUndertakingResponse(
            id=u.id,
            institution_id=u.institution_id,
            institution_name=u.institution.name if u.institution else None,
            application_id=u.application_id,
            title=u.title,
            category=u.category,
            description=u.description,
            due_date=u.due_date,
            status=u.status,
            effective_status=eff_status,
            rule_code=u.rule_code,
            responsible_user_id=u.responsible_user_id,
            reviewer_id=u.reviewer_id,
            evidence_type=u.evidence_type,
            fulfilled_at=u.fulfilled_at,
            verified_at=u.verified_at,
            verified_by_id=u.verified_by_id,
            created_at=u.created_at,
            evidences=[ComplianceEvidenceResponse.model_validate(e) for e in u.evidences]
        ))
    return results

@router.get("/undertakings/{id}", response_model=ComplianceUndertakingResponse)
def get_undertaking(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    undertaking = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.id == id).first()
    if not undertaking:
        raise HTTPException(status_code=404, detail="Compliance undertaking not found")

    check_institution_scope(current_user, undertaking.institution_id)
    if undertaking.institution:
        user_roles = [r.role for r in current_user.roles]
        if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
            check_regional_scope(current_user, undertaking.institution.region)

    eff_status = ComplianceService.get_effective_status(undertaking)
    return ComplianceUndertakingResponse(
        id=undertaking.id,
        institution_id=undertaking.institution_id,
        institution_name=undertaking.institution.name if undertaking.institution else None,
        application_id=undertaking.application_id,
        title=undertaking.title,
        category=undertaking.category,
        description=undertaking.description,
        due_date=undertaking.due_date,
        status=undertaking.status,
        effective_status=eff_status,
        rule_code=undertaking.rule_code,
        responsible_user_id=undertaking.responsible_user_id,
        reviewer_id=undertaking.reviewer_id,
        evidence_type=undertaking.evidence_type,
        fulfilled_at=undertaking.fulfilled_at,
        verified_at=undertaking.verified_at,
        verified_by_id=undertaking.verified_by_id,
        created_at=undertaking.created_at,
        evidences=[ComplianceEvidenceResponse.model_validate(e) for e in undertaking.evidences]
    )

@router.post("/undertakings", response_model=ComplianceUndertakingResponse, status_code=status.HTTP_201_CREATED)
def create_undertaking(
    request: ComplianceUndertakingCreate,
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))
):
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    verify_regional_access(inst.region, current_user)

    undertaking = ComplianceUndertaking(
        institution_id=inst.id,
        application_id=request.application_id,
        title=request.title,
        category=request.category,
        description=request.description,
        due_date=request.due_date,
        rule_code=request.rule_code,
        evidence_type=request.evidence_type or "PDF_DOCUMENT",
        status="NOT_YET_DUE"
    )
    db.add(undertaking)
    db.commit()
    db.refresh(undertaking)

    actor_role = current_user.roles[0].role if current_user.roles else "OFFICER"
    log_audit_event(
        db=db,
        action="UNDERTAKING_CREATED",
        entity_type="UNDERTAKING",
        entity_id=undertaking.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"title": undertaking.title, "due_date": request.due_date.isoformat()}
    )

    return ComplianceUndertakingResponse(
        id=undertaking.id,
        institution_id=undertaking.institution_id,
        institution_name=inst.name,
        application_id=undertaking.application_id,
        title=undertaking.title,
        category=undertaking.category,
        description=undertaking.description,
        due_date=undertaking.due_date,
        status=undertaking.status,
        effective_status="NOT_YET_DUE",
        rule_code=undertaking.rule_code,
        responsible_user_id=undertaking.responsible_user_id,
        reviewer_id=undertaking.reviewer_id,
        evidence_type=undertaking.evidence_type,
        fulfilled_at=undertaking.fulfilled_at,
        verified_at=undertaking.verified_at,
        verified_by_id=undertaking.verified_by_id,
        created_at=undertaking.created_at,
        evidences=[]
    )

@router.post("/undertakings/{id}/submit-evidence")
def submit_compliance_evidence(
    id: int,
    file: UploadFile = File(...),
    remarks: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"]))
):
    evidence = ComplianceService.submit_evidence(
        db=db,
        undertaking_id=id,
        file=file,
        remarks=remarks,
        actor=current_user
    )
    return {
        "message": "Compliance evidence submitted successfully",
        "version": evidence.version,
        "checksum": evidence.checksum_sha256,
        "file_name": evidence.file_name
    }

@router.post("/undertakings/{id}/verify")
def verify_compliance_evidence(
    id: int,
    request: ComplianceVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    undertaking = ComplianceService.verify_obligation(
        db=db,
        undertaking_id=id,
        outcome_status=request.status,
        notes=request.notes or "Compliance verification recorded.",
        actor=current_user
    )
    return {
        "message": f"Compliance evidence marked as {request.status}",
        "status": undertaking.status
    }

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.institution import Institution
from app.schemas.compliance import (
    ComplianceUndertakingResponse, ComplianceUndertakingCreate, ComplianceVerifyRequest
)
from app.services.document_service import save_uploaded_file
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/compliance", tags=["Compliance Passport"])

@router.get("/undertakings", response_model=List[ComplianceUndertakingResponse])
def list_undertakings(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
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

    undertakings = query.order_by(ComplianceUndertaking.due_date.asc()).all()
    results = []
    for u in undertakings:
        results.append(ComplianceUndertakingResponse(
            id=u.id,
            institution_id=u.institution_id,
            institution_name=u.institution.name,
            title=u.title,
            category=u.category,
            description=u.description,
            due_date=u.due_date,
            status=u.status,
            verified_at=u.verified_at,
            verified_by_id=u.verified_by_id,
            created_at=u.created_at,
            evidences=u.evidences
        ))
    return results

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
        title=request.title,
        category=request.category,
        description=request.description,
        due_date=request.due_date,
        status="NOT_YET_DUE"
    )
    db.add(undertaking)
    db.commit()
    db.refresh(undertaking)

    log_audit_event(
        db=db,
        action="UNDERTAKING_CREATED",
        entity_type="UNDERTAKING",
        entity_id=undertaking.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.roles[0].role if current_user.roles else "OFFICER",
        details={"title": undertaking.title, "due_date": request.due_date.isoformat()}
    )

    return ComplianceUndertakingResponse(
        id=undertaking.id,
        institution_id=undertaking.institution_id,
        institution_name=inst.name,
        title=undertaking.title,
        category=undertaking.category,
        description=undertaking.description,
        due_date=undertaking.due_date,
        status=undertaking.status,
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
    undertaking = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.id == id).first()
    if not undertaking:
        raise HTTPException(status_code=404, detail="Compliance undertaking not found")

    verify_institution_access(undertaking.institution_id, current_user)

    orig_name, file_url, checksum = save_uploaded_file(file)

    current_count = len(undertaking.evidences)
    new_version = current_count + 1

    evidence = ComplianceEvidence(
        undertaking_id=undertaking.id,
        version=new_version,
        file_name=orig_name,
        file_url=file_url,
        checksum_sha256=checksum,
        remarks=remarks,
        submitted_by_id=current_user.id,
        submitted_at=datetime.now(timezone.utc)
    )
    db.add(evidence)
    
    # Update undertaking status to pending verification
    undertaking.status = "PENDING_VERIFICATION"
    db.commit()

    actor_role = current_user.roles[0].role if current_user.roles else "COMPLIANCE_OFFICER"
    log_audit_event(
        db=db,
        action="COMPLIANCE_EVIDENCE_SUBMITTED",
        entity_type="UNDERTAKING",
        entity_id=undertaking.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"version": new_version, "file_name": orig_name, "checksum": checksum}
    )

    return {"message": "Compliance evidence submitted successfully", "version": new_version, "checksum": checksum}

@router.post("/undertakings/{id}/verify")
def verify_compliance_evidence(
    id: int,
    request: ComplianceVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    undertaking = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.id == id).first()
    if not undertaking:
        raise HTTPException(status_code=404, detail="Compliance undertaking not found")

    if undertaking.institution:
        verify_regional_access(undertaking.institution.region, current_user)

    if request.status not in ["VERIFIED", "DEFICIENT"]:
        raise HTTPException(status_code=400, detail="Status must be either 'VERIFIED' or 'DEFICIENT'")

    undertaking.status = request.status
    now = datetime.now(timezone.utc)
    if request.status == "VERIFIED":
        undertaking.verified_at = now
        undertaking.verified_by_id = current_user.id
    
    db.commit()

    actor_role = current_user.roles[0].role if current_user.roles else "REGIONAL_OFFICER"
    log_audit_event(
        db=db,
        action="COMPLIANCE_EVIDENCE_VERIFIED",
        entity_type="UNDERTAKING",
        entity_id=undertaking.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"outcome": request.status, "notes": request.notes}
    )

    return {"message": f"Compliance evidence marked as {request.status}", "status": request.status}

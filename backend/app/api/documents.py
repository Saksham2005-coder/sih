import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timezone
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.document import DocumentRecord, DocumentVersion
from app.models.compliance import ComplianceEvidence, ComplianceUndertaking
from app.models.institution import Institution
from app.schemas.document import DocumentRecordResponse, DocumentVerifyRequest, DocumentRecordCreate, DocumentVersionResponse
from app.services.document_service import StorageService
from app.services.audit_service import log_audit_event
from app.core.rbac import check_institution_scope, check_regional_scope, has_permission, Permission

router = APIRouter(prefix="/documents", tags=["Documents & Renewals"])

@router.get("", response_model=List[DocumentRecordResponse])
def list_documents(
    document_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DocumentRecord).join(Institution, DocumentRecord.institution_id == Institution.id)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(DocumentRecord.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(Institution.region == current_user.region)

    if document_type:
        query = query.filter(DocumentRecord.document_type == document_type)
    if status_filter:
        query = query.filter(DocumentRecord.status == status_filter)
    if application_id:
        query = query.filter(DocumentRecord.application_id == application_id)

    records = query.order_by(DocumentRecord.expiry_date.asc().nullslast()).all()
    results = []
    for d in records:
        results.append(DocumentRecordResponse(
            id=d.id,
            institution_id=d.institution_id,
            institution_name=d.institution.name if d.institution else None,
            application_id=d.application_id,
            document_type=d.document_type,
            title=d.title,
            document_number=d.document_number,
            issuing_authority=d.issuing_authority,
            issue_date=d.issue_date,
            valid_from=d.valid_from,
            expiry_date=d.expiry_date,
            renewal_required=d.renewal_required,
            status=d.status,
            current_version=d.current_version,
            created_at=d.created_at,
            versions=[DocumentVersionResponse.model_validate(v) for v in d.versions]
        ))
    return results

@router.post("", response_model=DocumentRecordResponse, status_code=status.HTTP_201_CREATED)
def create_document_record(
    request: DocumentRecordCreate,
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_inst_id = institution_id or current_user.institution_id
    if not target_inst_id:
        raise HTTPException(status_code=400, detail="Institution ID is required")

    check_institution_scope(current_user, target_inst_id)

    if not has_permission(current_user, Permission.DOCUMENT_UPLOAD):
        raise HTTPException(status_code=403, detail="Unauthorized: User does not hold 'document.upload' permission")

    inst = db.query(Institution).filter(Institution.id == target_inst_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    doc = DocumentRecord(
        institution_id=inst.id,
        application_id=request.application_id,
        document_type=request.document_type,
        title=request.title,
        document_number=request.document_number,
        issuing_authority=request.issuing_authority,
        issue_date=request.issue_date,
        valid_from=request.valid_from,
        expiry_date=request.expiry_date,
        renewal_required=request.renewal_required,
        status="ACTIVE",
        current_version=1
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    actor_role = current_user.roles[0].role if current_user.roles else "INSTITUTION_ADMIN"
    log_audit_event(
        db=db,
        action="DOCUMENT_RECORD_CREATED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={"title": doc.title, "document_type": doc.document_type}
    )

    return DocumentRecordResponse(
        id=doc.id,
        institution_id=doc.institution_id,
        institution_name=inst.name,
        application_id=doc.application_id,
        document_type=doc.document_type,
        title=doc.title,
        document_number=doc.document_number,
        issuing_authority=doc.issuing_authority,
        issue_date=doc.issue_date,
        valid_from=doc.valid_from,
        expiry_date=doc.expiry_date,
        renewal_required=doc.renewal_required,
        status=doc.status,
        current_version=doc.current_version,
        created_at=doc.created_at,
        versions=[]
    )

@router.post("/{id}/renew")
def submit_document_renewal(
    id: int,
    file: UploadFile = File(...),
    new_expiry_date: Optional[str] = Form(None), # YYYY-MM-DD
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"]))
):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    # Authorize institution scope
    check_institution_scope(current_user, doc.institution_id)

    if not has_permission(current_user, Permission.DOCUMENT_UPLOAD):
        raise HTTPException(status_code=403, detail="Unauthorized: User does not hold 'document.upload' permission")

    # Save to storage with validation
    meta = StorageService.validate_and_save(file)

    try:
        new_version_num = doc.current_version + 1
        doc.current_version = new_version_num
        doc.status = "RENEWAL_SUBMITTED"

        if new_expiry_date:
            try:
                parsed_expiry = datetime.strptime(new_expiry_date, "%Y-%m-%d").date()
                doc.expiry_date = parsed_expiry
            except ValueError:
                pass

        version = DocumentVersion(
            document_record_id=doc.id,
            version=new_version_num,
            file_name=meta["file_name"],
            file_url=meta["file_url"],
            storage_key=meta["storage_key"],
            file_size=meta["file_size"],
            mime_type=meta["mime_type"],
            checksum_sha256=meta["checksum_sha256"],
            renewal_reason=notes,
            uploaded_by_id=current_user.id,
            uploaded_at=datetime.now(timezone.utc),
            verification_status="PENDING",
            verification_notes=notes
        )
        db.add(version)
        db.commit()

        actor_role = current_user.roles[0].role if current_user.roles else "INSTITUTION_ADMIN"
        log_audit_event(
            db=db,
            action="DOCUMENT_RENEWAL_SUBMITTED",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            actor_id=current_user.id,
            actor_name=current_user.full_name,
            actor_role=actor_role,
            details={
                "version": new_version_num,
                "file_name": meta["file_name"],
                "checksum": meta["checksum_sha256"],
                "file_size": meta["file_size"]
            }
        )

        return {
            "message": "Document renewal submitted successfully",
            "version": new_version_num,
            "checksum": meta["checksum_sha256"],
            "file_name": meta["file_name"]
        }

    except Exception as e:
        db.rollback()
        StorageService.cleanup_file(meta["local_path"])
        raise HTTPException(status_code=500, detail=f"Failed to submit document renewal: {str(e)}")

@router.post("/{id}/verify-version/{version_id}")
def verify_document_version(
    id: int,
    version_id: int,
    request: DocumentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    if doc.institution:
        check_regional_scope(current_user, doc.institution.region)

    if not has_permission(current_user, Permission.DOCUMENT_VERIFY):
        raise HTTPException(status_code=403, detail="Unauthorized: User does not hold 'document.verify' permission")

    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_record_id == doc.id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")

    if request.verification_status not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="verification_status must be 'VERIFIED' or 'REJECTED'")

    if not request.verification_notes or not request.verification_notes.strip():
        raise HTTPException(status_code=400, detail="Verification notes are mandatory.")

    version.verification_status = request.verification_status
    version.verification_notes = request.verification_notes.strip()
    version.verified_by_id = current_user.id
    version.verified_at = datetime.now(timezone.utc)

    # Invariant: Rejection does NOT extend expiry
    if request.verification_status == "VERIFIED":
        doc.status = "ACTIVE"
    else:
        # Check if expired
        today = date.today()
        if doc.expiry_date and doc.expiry_date < today:
            doc.status = "EXPIRED"
        else:
            doc.status = "EXPIRING_SOON"

    db.commit()

    actor_role = current_user.roles[0].role if current_user.roles else "REGIONAL_OFFICER"
    log_audit_event(
        db=db,
        action="DOCUMENT_VERSION_VERIFIED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=actor_role,
        details={
            "version_id": version.id,
            "version_number": version.version,
            "outcome": request.verification_status,
            "doc_status": doc.status
        }
    )

    return {"message": f"Document version marked as {request.verification_status}", "doc_status": doc.status}

@router.get("/download/{filename}")
def download_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Sanitize filename to prevent directory traversal
    clean_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, clean_filename))
    base_upload_path = os.path.abspath(settings.UPLOAD_DIR)

    if not file_path.startswith(base_upload_path) or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested file not found on server")

    # 2. Resource-level access authorization check
    # Locate owning entity (DocumentVersion or ComplianceEvidence)
    owning_inst_id = None
    owning_region = None

    doc_version = db.query(DocumentVersion).join(
        DocumentRecord, DocumentVersion.document_record_id == DocumentRecord.id
    ).join(
        Institution, DocumentRecord.institution_id == Institution.id
    ).filter(
        (DocumentVersion.storage_key == clean_filename) |
        (DocumentVersion.file_url.endswith(clean_filename))
    ).first()

    if doc_version:
        owning_inst_id = doc_version.document_record.institution_id
        owning_region = doc_version.document_record.institution.region if doc_version.document_record.institution else None

    if not owning_inst_id:
        comp_ev = db.query(ComplianceEvidence).join(
            ComplianceUndertaking, ComplianceEvidence.undertaking_id == ComplianceUndertaking.id
        ).join(
            Institution, ComplianceUndertaking.institution_id == Institution.id
        ).filter(
            ComplianceEvidence.file_url.endswith(clean_filename)
        ).first()

        if comp_ev:
            owning_inst_id = comp_ev.undertaking.institution_id
            owning_region = comp_ev.undertaking.institution.region if comp_ev.undertaking.institution else None

    # Check access scope if owning institution identified
    if owning_inst_id:
        user_roles = [r.role for r in current_user.roles]
        is_officer = any(r in [
            "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
            "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
        ] for r in user_roles)

        if not is_officer:
            if current_user.institution_id != owning_inst_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have permission to download documents belonging to this institution."
                )
        elif "REGIONAL_OFFICER" in user_roles and owning_region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
            if current_user.region and current_user.region != owning_region:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Regional Officer cannot download documents outside assigned region."
                )

    return FileResponse(path=file_path, filename=clean_filename)

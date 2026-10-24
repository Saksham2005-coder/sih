import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timezone
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access
from app.models.user import User
from app.models.document import DocumentRecord, DocumentVersion
from app.models.institution import Institution
from app.schemas.document import DocumentRecordResponse, DocumentVerifyRequest
from app.services.document_service import save_uploaded_file
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/documents", tags=["Documents & Renewals"])

@router.get("", response_model=List[DocumentRecordResponse])
def list_documents(
    document_type: Optional[str] = None,
    status_filter: Optional[str] = None,
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

    records = query.order_by(DocumentRecord.expiry_date.asc()).all()
    results = []
    for d in records:
        results.append(DocumentRecordResponse(
            id=d.id,
            institution_id=d.institution_id,
            institution_name=d.institution.name,
            document_type=d.document_type,
            title=d.title,
            document_number=d.document_number,
            issue_date=d.issue_date,
            expiry_date=d.expiry_date,
            status=d.status,
            current_version=d.current_version,
            created_at=d.created_at,
            versions=d.versions
        ))
    return results

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

    verify_institution_access(doc.institution_id, current_user)

    orig_name, file_url, checksum = save_uploaded_file(file)

    new_version_num = doc.current_version + 1
    doc.current_version = new_version_num
    doc.status = "RENEWAL_SUBMITTED"

    if new_expiry_date:
        try:
            doc.expiry_date = datetime.strptime(new_expiry_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    version = DocumentVersion(
        document_record_id=doc.id,
        version=new_version_num,
        file_name=orig_name,
        file_url=file_url,
        checksum_sha256=checksum,
        uploaded_by_id=current_user.id,
        uploaded_at=datetime.now(timezone.utc),
        verification_status="PENDING",
        verification_notes=notes
    )
    db.add(version)
    db.commit()

    log_audit_event(
        db=db,
        action="DOCUMENT_RENEWAL_SUBMITTED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="INSTITUTION_ADMIN",
        details={"version": new_version_num, "file_name": orig_name, "checksum": checksum}
    )

    return {"message": "Document renewal submitted successfully", "version": new_version_num, "checksum": checksum}

@router.post("/{id}/verify-version/{version_id}")
def verify_document_version(
    id: int,
    version_id: int,
    request: DocumentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))
):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == version_id,
        DocumentVersion.document_record_id == doc.id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")

    version.verification_status = request.verification_status
    version.verification_notes = request.verification_notes
    version.verified_by_id = current_user.id
    version.verified_at = datetime.now(timezone.utc)

    if request.verification_status == "VERIFIED":
        doc.status = "ACTIVE"
    else:
        doc.status = "EXPIRING_SOON"

    db.commit()

    log_audit_event(
        db=db,
        action="DOCUMENT_VERSION_VERIFIED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="REGIONAL_OFFICER",
        details={"version_id": version.id, "outcome": request.verification_status}
    )

    return {"message": f"Document version marked as {request.verification_status}", "doc_status": doc.status}

@router.get("/download/{filename}")
def download_file(filename: str):
    # Sanitize filename to prevent directory traversal
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(settings.UPLOAD_DIR, clean_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested file not found on server")
    return FileResponse(path=file_path, filename=clean_filename)

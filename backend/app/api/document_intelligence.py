from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.document import DocumentRecord, DocumentVersion
from app.models.document_analysis import DocumentAnalysis
from app.models.institution import Institution
from app.schemas.document_analysis import (
    DocumentAnalysisResponse,
    DocumentAnalysisReviewRequest,
    DocumentAnalysisTriggerRequest,
    CrossCheckFinding
)
from app.services.document_intelligence_service import DocumentIntelligenceService
from app.core.rbac import check_institution_scope, check_regional_scope, has_permission, Permission

router = APIRouter(prefix="/documents/analysis", tags=["Document Intelligence & Cross-Checking"])


def format_analysis_response(a: DocumentAnalysis) -> DocumentAnalysisResponse:
    inst_name = a.institution.name if a.institution else None
    reviewer_name = a.reviewer.full_name if a.reviewer else None

    # Parse findings into CrossCheckFinding schema
    findings_objs = []
    for f in (a.cross_check_findings or []):
        if isinstance(f, dict):
            findings_objs.append(CrossCheckFinding(**f))

    return DocumentAnalysisResponse(
        id=a.id,
        document_record_id=a.document_record_id,
        document_version_id=a.document_version_id,
        compliance_evidence_id=a.compliance_evidence_id,
        institution_id=a.institution_id,
        institution_name=inst_name,
        status=a.status,
        idempotency_key=a.idempotency_key,
        extraction_engine=a.extraction_engine,
        engine_version=a.engine_version,
        ocr_applied=a.ocr_applied,
        ocr_provider=a.ocr_provider,
        file_name=a.file_name,
        file_size=a.file_size,
        checksum_sha256=a.checksum_sha256,
        page_count=a.page_count,
        has_text_layer=a.has_text_layer,
        is_scanned=a.is_scanned,
        extracted_fields=a.extracted_fields or {},
        cross_check_findings=findings_objs,
        overall_confidence=a.overall_confidence or 0.0,
        summary_findings=a.summary_findings,
        error_message=a.error_message,
        reviewer_decision=a.reviewer_decision,
        reviewed_by_id=a.reviewed_by_id,
        reviewed_by_name=reviewer_name,
        reviewed_at=a.reviewed_at,
        reviewer_remarks=a.reviewer_remarks,
        corrected_fields=a.corrected_fields,
        processing_started_at=a.processing_started_at,
        processing_completed_at=a.processing_completed_at,
        created_at=a.created_at,
        updated_at=a.updated_at
    )


@router.get("", response_model=List[DocumentAnalysisResponse])
def list_document_analyses(
    status_filter: Optional[str] = Query(None, alias="status"),
    institution_id: Optional[int] = None,
    document_record_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DocumentAnalysis).join(Institution, DocumentAnalysis.institution_id == Institution.id)

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return []
        query = query.filter(DocumentAnalysis.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and current_user.region and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        query = query.filter(Institution.region == current_user.region)

    if institution_id:
        if not is_officer and current_user.institution_id != institution_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot query analyses for another institution.")
        query = query.filter(DocumentAnalysis.institution_id == institution_id)

    if status_filter:
        query = query.filter(DocumentAnalysis.status == status_filter)

    if document_record_id:
        query = query.filter(DocumentAnalysis.document_record_id == document_record_id)

    analyses = query.order_by(DocumentAnalysis.created_at.desc()).limit(100).all()
    return [format_analysis_response(a) for a in analyses]


@router.get("/{id}", response_model=DocumentAnalysisResponse)
def get_document_analysis(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Document analysis record not found")

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if current_user.institution_id != analysis.institution_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access document intelligence for another institution.")
    elif "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if analysis.institution and current_user.region and current_user.region != analysis.institution.region:
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer cannot view analysis outside assigned region.")

    return format_analysis_response(analysis)


@router.get("/by-version/{version_id}", response_model=DocumentAnalysisResponse)
def get_analysis_by_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")

    doc = version.document_record
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if current_user.institution_id != doc.institution_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access document version belonging to another institution.")
    elif "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if doc.institution and current_user.region and current_user.region != doc.institution.region:
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer cannot view document version outside assigned region.")

    # Fetch existing or trigger analysis
    analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_version_id == version.id).first()
    if not analysis:
        analysis = DocumentIntelligenceService.analyze_document_version(
            db=db,
            document_version_id=version.id,
            force_retry=False
        )

    return format_analysis_response(analysis)


@router.post("/trigger", response_model=DocumentAnalysisResponse)
def trigger_document_analysis(
    request: DocumentAnalysisTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version_id = request.document_version_id

    # If document_record_id provided without version_id, use latest version
    if not version_id and request.document_record_id:
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == request.document_record_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document record not found")
        if doc.versions:
            sorted_v = sorted(doc.versions, key=lambda v: v.version, reverse=True)
            version_id = sorted_v[0].id
        else:
            raise HTTPException(status_code=400, detail="Document record has no uploaded versions to analyze.")

    if not version_id:
        raise HTTPException(status_code=400, detail="Must provide either document_version_id or document_record_id.")

    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")

    doc = version.document_record
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if current_user.institution_id != doc.institution_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot trigger analysis on another institution's document.")
    elif "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if doc.institution and current_user.region and current_user.region != doc.institution.region:
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer cannot trigger analysis outside assigned region.")

    analysis = DocumentIntelligenceService.analyze_document_version(
        db=db,
        document_version_id=version.id,
        force_retry=request.force_retry
    )

    return format_analysis_response(analysis)


@router.post("/{id}/review", response_model=DocumentAnalysisResponse)
def review_document_analysis(
    id: int,
    request: DocumentAnalysisReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER"]))
):
    analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Document analysis record not found")

    # Scope check
    if "REGIONAL_OFFICER" in [r.role for r in current_user.roles] and "BUREAU_OFFICER" not in [r.role for r in current_user.roles]:
        if analysis.institution and current_user.region and current_user.region != analysis.institution.region:
            raise HTTPException(status_code=403, detail="Access denied: Regional Officer cannot review document analysis outside assigned region.")

    updated_analysis = DocumentIntelligenceService.review_and_confirm_analysis(
        db=db,
        analysis_id=analysis.id,
        decision=request.decision,
        remarks=request.reviewer_remarks,
        reviewer=current_user,
        corrected_fields=request.corrected_fields,
        apply_to_record=request.apply_to_record
    )

    return format_analysis_response(updated_analysis)

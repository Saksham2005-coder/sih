import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_institution_access, verify_regional_access
from app.models.user import User
from app.models.application import Application
from app.models.statutory_order import StatutoryOrder
from app.schemas.statutory_order import (
    StatutoryOrderGenerateRequest,
    StatutoryOrderRevokeRequest,
    StatutoryOrderResponse,
    StatutoryOrderPublicVerificationResponse,
    OrderArtifactVerifyUploadResponse,
)
from app.services.order_generation_service import OrderGenerationService
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/orders", tags=["Statutory Orders & Integrity Verification"])


@router.post("/generate", response_model=StatutoryOrderResponse, status_code=status.HTTP_201_CREATED)
def generate_order(
    req: StatutoryOrderGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["COMPETENT_AUTHORITY"]))
):
    """
    Generates a formal statutory approval or rejection order PDF artifact.
    Strictly restricted to Competent Authority. SYSTEM_ADMIN receives HTTP 403.
    Can only be invoked after a statutory decision has been recorded on the application.
    """
    # Derive frontend verification base URL
    frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    verification_base_url = f"{frontend_base.rstrip('/')}/verify-order"

    try:
        order = OrderGenerationService.generate_statutory_order(
            db=db,
            request=req,
            current_user=current_user,
            base_verification_url=verification_base_url
        )

        return StatutoryOrderResponse.model_validate(order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order generation failed: {str(e)}"
        )


@router.post("/{order_id}/revoke", response_model=StatutoryOrderResponse)
def revoke_order(
    order_id: int,
    req: StatutoryOrderRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["COMPETENT_AUTHORITY"]))
):
    """
    Revokes an issued statutory order with a mandatory administrative reason.
    Strictly restricted to Competent Authority. SYSTEM_ADMIN receives HTTP 403.
    """
    order = OrderGenerationService.revoke_order(
        db=db,
        order_id=order_id,
        current_user=current_user,
        reason=req.revocation_reason
    )

    return StatutoryOrderResponse.model_validate(order)


@router.get("/by-application/{application_id}", response_model=List[StatutoryOrderResponse])
def get_orders_by_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all statutory order artifacts (active, superseded, revoked) for a specific application.
    Enforces tenant and regional access boundaries.
    """
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )

    # Multi-tenant and regional isolation checks
    verify_institution_access(app_record.institution_id, current_user)
    verify_regional_access(app_record.institution.region if app_record.institution else None, current_user)

    orders = db.query(StatutoryOrder).filter(
        StatutoryOrder.application_id == application_id
    ).order_by(StatutoryOrder.version.desc()).all()

    return [StatutoryOrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}/download")
def download_order_pdf(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Securely streams the PDF artifact for an authorized order.
    Enforces multi-tenant and regional isolation boundaries.
    """
    order = db.query(StatutoryOrder).filter(StatutoryOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statutory order {order_id} not found"
        )

    # Scoping check
    verify_institution_access(order.institution_id, current_user)
    app_record = db.query(Application).filter(Application.id == order.application_id).first()
    if app_record and app_record.institution:
        verify_regional_access(app_record.institution.region, current_user)

    file_path = order.pdf_storage_key
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order PDF artifact file not found on disk"
        )

    actor_role = "USER"
    if current_user and hasattr(current_user, "roles") and current_user.roles:
        actor_role = current_user.roles[0].role

    log_audit_event(
        db=db,
        action="STATUTORY_ORDER_DOWNLOADED",
        entity_type="STATUTORY_ORDER",
        entity_id=order.id,
        actor_id=current_user.id if current_user else None,
        actor_name=current_user.full_name if current_user else None,
        actor_role=actor_role,
        institution_id=order.institution_id,
        details={
            "order_number": order.order_number,
            "version": order.version,
            "checksum_sha256": order.checksum_sha256
        }
    )

    return FileResponse(
        path=file_path,
        filename=order.pdf_filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{order.pdf_filename}"',
            "X-Order-Checksum-SHA256": order.checksum_sha256,
            "X-Order-Version": str(order.version),
            "X-Signature-Status": order.signature_status
        }
    )


@router.get("/verify/{token}", response_model=StatutoryOrderPublicVerificationResponse)
def verify_order_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Public-safe verification endpoint for statutory decision orders.
    Scanned from the document's QR code or entered on the verification portal.
    Discloses only minimal public verification facts without leaking confidential dossiers.
    """
    return OrderGenerationService.verify_order_by_token(db=db, verification_token=token)


@router.post("/verify-upload", response_model=OrderArtifactVerifyUploadResponse)
async def verify_order_by_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Public-safe artifact integrity verification via file upload.
    Computes cryptographic SHA-256 hash of the uploaded document and matches against
    the immutable registered artifact hash in the database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents can be verified against statutory order records"
        )

    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum verification limit (25 MB)"
        )

    return OrderGenerationService.verify_order_by_file_content(db=db, file_content=content)

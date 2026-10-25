from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.institution import Institution
from app.models.user import User
from app.models.alert import Notification
from app.services.document_service import StorageService
from app.services.audit_service import log_audit_event
from app.core.rbac import check_institution_scope, check_regional_scope, Permission, has_permission

VALID_VERIFICATION_STATUSES = {"VERIFIED", "CORRECTION_REQUIRED", "DEFICIENT"}

class ComplianceService:
    """
    Central authoritative service for Institutional Compliance Passport lifecycle.
    """

    @staticmethod
    def submit_evidence(
        db: Session,
        undertaking_id: int,
        file: UploadFile,
        remarks: Optional[str],
        actor: User
    ) -> ComplianceEvidence:
        undertaking = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.id == undertaking_id).first()
        if not undertaking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance undertaking not found")

        # 1. Authorize institution scope
        check_institution_scope(actor, undertaking.institution_id)

        # 2. Check permission
        if not has_permission(actor, Permission.COMPLIANCE_SUBMIT):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: User does not hold 'compliance.submit' permission."
            )

        # 3. Validate and store file
        meta = StorageService.validate_and_save(file)

        try:
            # Determine new version
            current_max_version = db.query(ComplianceEvidence).filter(
                ComplianceEvidence.undertaking_id == undertaking.id
            ).count()
            new_version = current_max_version + 1

            evidence = ComplianceEvidence(
                undertaking_id=undertaking.id,
                version=new_version,
                file_name=meta["file_name"],
                file_url=meta["file_url"],
                checksum_sha256=meta["checksum_sha256"],
                remarks=remarks,
                submitted_by_id=actor.id,
                submitted_at=datetime.now(timezone.utc),
                verification_status="PENDING"
            )
            db.add(evidence)

            # Update undertaking lifecycle status
            undertaking.status = "PENDING_VERIFICATION"
            now = datetime.now(timezone.utc)

            # Audit event
            actor_role = actor.roles[0].role if actor.roles else "COMPLIANCE_OFFICER"
            log_audit_event(
                db=db,
                action="COMPLIANCE_EVIDENCE_SUBMITTED",
                entity_type="UNDERTAKING",
                entity_id=undertaking.id,
                actor_id=actor.id,
                actor_name=actor.full_name,
                actor_role=actor_role,
                details={
                    "version": new_version,
                    "file_name": meta["file_name"],
                    "checksum": meta["checksum_sha256"],
                    "file_size": meta["file_size"]
                }
            )

            # Notification for regional office
            if undertaking.institution:
                notif = Notification(
                    institution_id=undertaking.institution_id,
                    title=f"Evidence submitted for: {undertaking.title}",
                    message=f"Version {new_version} of evidence submitted by {actor.full_name}.",
                    level="INFO",
                    link_url=f"/compliance"
                )
                db.add(notif)

            db.commit()
            db.refresh(evidence)
            return evidence

        except Exception as e:
            db.rollback()
            # Clean up stored file to prevent orphaned files
            StorageService.cleanup_file(meta["local_path"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record compliance evidence: {str(e)}"
            )

    @staticmethod
    def verify_obligation(
        db: Session,
        undertaking_id: int,
        outcome_status: str,
        notes: str,
        actor: User
    ) -> ComplianceUndertaking:
        undertaking = db.query(ComplianceUndertaking).filter(ComplianceUndertaking.id == undertaking_id).first()
        if not undertaking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance undertaking not found")

        # 1. Scope check (Regional Officer must be in-region)
        if undertaking.institution:
            check_regional_scope(actor, undertaking.institution.region)

        # 2. Permission check
        if not has_permission(actor, Permission.COMPLIANCE_VERIFY):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: User does not hold 'compliance.verify' permission."
            )

        # 3. Prohibit self-verification by institution
        user_roles = [r.role for r in actor.roles]
        if any(r in ["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"] for r in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-verification prohibited: Institution users cannot verify compliance obligations."
            )

        # 4. Outcome validation
        if outcome_status not in VALID_VERIFICATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification status '{outcome_status}'. Must be one of: {', '.join(sorted(VALID_VERIFICATION_STATUSES))}"
            )

        # 5. Mandatory notes check
        if not notes or not notes.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification notes/remarks are mandatory when recording a compliance determination."
            )

        now = datetime.now(timezone.utc)
        undertaking.status = outcome_status

        if outcome_status == "VERIFIED":
            undertaking.verified_at = now
            undertaking.verified_by_id = actor.id
            undertaking.fulfilled_at = now
        elif outcome_status in ["CORRECTION_REQUIRED", "DEFICIENT"]:
            undertaking.verified_at = None
            undertaking.verified_by_id = None
            undertaking.fulfilled_at = None

        # Update latest evidence version if exists
        latest_evidence = db.query(ComplianceEvidence).filter(
            ComplianceEvidence.undertaking_id == undertaking.id
        ).order_by(ComplianceEvidence.version.desc()).first()

        if latest_evidence:
            latest_evidence.verification_status = outcome_status
            latest_evidence.verified_by_id = actor.id
            latest_evidence.verified_at = now
            latest_evidence.verification_notes = notes

        # Audit log
        actor_role = actor.roles[0].role if actor.roles else "REGIONAL_OFFICER"
        log_audit_event(
            db=db,
            action=f"COMPLIANCE_OBLIGATION_{outcome_status}",
            entity_type="UNDERTAKING",
            entity_id=undertaking.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "outcome": outcome_status,
                "notes": notes,
                "evidence_version": latest_evidence.version if latest_evidence else None
            }
        )

        # Institution notification
        notif_level = "SUCCESS" if outcome_status == "VERIFIED" else ("WARNING" if outcome_status == "CORRECTION_REQUIRED" else "DANGER")
        notif = Notification(
            institution_id=undertaking.institution_id,
            title=f"Compliance Undertaking '{undertaking.title}' marked as {outcome_status}",
            message=notes,
            level=notif_level,
            link_url=f"/compliance"
        )
        db.add(notif)

        db.commit()
        db.refresh(undertaking)
        return undertaking

    @staticmethod
    def get_effective_status(undertaking: ComplianceUndertaking) -> str:
        """
        Derives time-aware status without destroying pending verification submissions.
        """
        now = datetime.now(timezone.utc)
        if undertaking.status == "VERIFIED":
            return "VERIFIED"
        if undertaking.status == "PENDING_VERIFICATION":
            return "PENDING_VERIFICATION"
        if undertaking.status == "CORRECTION_REQUIRED":
            return "CORRECTION_REQUIRED"
        if undertaking.due_date:
            due = undertaking.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if now > due:
                return "OVERDUE"
            elif (due - now).days <= 15:
                return "DUE_SOON"
        return undertaking.status

import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.evc import EVCInspection, EVCExpert, EVCPanelAssignment, EVCFieldEvidence
from app.models.application import Application
from app.models.institution import Institution
from app.models.user import User
from app.services.workflow_engine import execute_transition
from app.services.audit_service import log_audit_event
from app.services.notification.outbox_dispatcher import OutboxDispatcherService
from app.core.rbac import check_regional_scope, has_permission, Permission

logger = logging.getLogger(__name__)

# Configurable illustrative conflict policy defaults
DEFAULT_COOLING_OFF_YEARS = 3
REQUIRED_PANEL_ROLES = ["CONVENER", "EXPERT_MEMBER"]


class EVCConflictService:
    """
    Explainable Conflict-of-Interest (COI) engine for EVC expert panel appointments.
    Evaluates auditable expert profile attributes against applicant institutions.
    Returns clear rule-by-rule assessments without black-box inferences.
    """

    @classmethod
    def evaluate_coi(
        cls,
        expert: EVCExpert,
        application: Application,
        cooling_off_years: int = DEFAULT_COOLING_OFF_YEARS
    ) -> Dict[str, Any]:
        """
        Executes configured COI rules:
        1. Same institutional affiliation (disallowed).
        2. Shared parent trust/society affiliation.
        3. Declared voluntary conflicts registry.
        4. Prior inspection cooling-off period (illustrative 3-year demonstration norm).
        5. Expert availability and active status.
        """
        now = datetime.now(timezone.utc)
        rules_checked = []

        # Source Data Verification: Distinguish true no-conflict from incomplete source data
        incompleteness_reasons = []
        if not application:
            incompleteness_reasons.append("Application record is missing.")
        elif not application.institution:
            incompleteness_reasons.append("Applicant institution record is unlinked or missing.")
        elif not (application.institution.name or "").strip():
            incompleteness_reasons.append("Applicant institution name is unrecorded.")

        if not expert:
            incompleteness_reasons.append("Expert registry profile is missing.")
        elif not (expert.current_institution or "").strip():
            incompleteness_reasons.append("Expert institutional affiliation is missing.")

        if incompleteness_reasons:
            return {
                "expert_id": expert.id if expert else 0,
                "expert_name": expert.name if expert else "Unknown",
                "current_institution": expert.current_institution if expert else "",
                "is_prohibited": True,  # Fail closed when source data is missing
                "can_override": False,
                "summary": f"Conflict-of-Interest assessment could not be completed because source data is missing: {'; '.join(incompleteness_reasons)}",
                "rules_checked": [
                    {
                        "rule_code": "DATA_COMPLETENESS",
                        "rule_name": "Applicant & Expert Affiliation Data Completeness",
                        "status": "FAILED",
                        "details": f"Missing regulatory source data: {'; '.join(incompleteness_reasons)}"
                    }
                ],
                "assessed_at": now.isoformat(),
                "data_completeness": "INCOMPLETE"
            }

        inst = application.institution
        is_prohibited = False

        inst_name = (inst.name if inst else "").strip().lower()
        inst_id = inst.id if inst else None
        expert_inst = (expert.current_institution or "").strip().lower()

        # Rule 1: Same Institutional Affiliation
        same_inst = False
        if expert.institution_id and inst_id and expert.institution_id == inst_id:
            same_inst = True
        elif expert_inst and inst_name and (expert_inst == inst_name or inst_name in expert_inst or expert_inst in inst_name):
            same_inst = True

        if same_inst:
            is_prohibited = True
            rules_checked.append({
                "rule_code": "SAME_INSTITUTION_AFFILIATION",
                "rule_name": "Prohibition of Same Institutional Affiliation (Illustrative APH Norm)",
                "status": "FAILED",
                "details": f"Expert affiliation '{expert.current_institution}' matches applicant institution '{inst.name if inst else 'Unknown'}'."
            })
        else:
            rules_checked.append({
                "rule_code": "SAME_INSTITUTION_AFFILIATION",
                "rule_name": "Prohibition of Same Institutional Affiliation (Illustrative APH Norm)",
                "status": "PASSED",
                "details": f"Expert affiliation '{expert.current_institution}' is distinct from applicant institution."
            })

        # Rule 2: Shared Parent Trust / Society
        shared_trust = False
        expert_parent = (expert.parent_organization or "").strip().lower()
        if expert_parent and inst:
            trust_candidates = [
                getattr(inst, "trust_name", "") or "",
                getattr(inst, "parent_trust", "") or "",
                getattr(inst, "society_name", "") or ""
            ]
            for tc in trust_candidates:
                tc_norm = tc.strip().lower()
                if tc_norm and (tc_norm == expert_parent or tc_norm in expert_parent or expert_parent in tc_norm):
                    shared_trust = True
                    break

        if shared_trust:
            is_prohibited = True
            rules_checked.append({
                "rule_code": "PARENT_TRUST_AFFILIATION",
                "rule_name": "Shared Parent Trust / Governing Society Affiliation",
                "status": "FAILED",
                "details": f"Expert parent organization '{expert.parent_organization}' matches applicant governing trust."
            })
        else:
            rules_checked.append({
                "rule_code": "PARENT_TRUST_AFFILIATION",
                "rule_name": "Shared Parent Trust / Governing Society Affiliation",
                "status": "PASSED",
                "details": "No shared parent trust or governing society affiliation detected."
            })

        # Rule 3: Declared Conflicts Registry
        declared_match = None
        for conflict in (expert.declared_conflicts or []):
            conf_inst_id = conflict.get("institution_id")
            conf_inst_name = (conflict.get("institution_name") or "").strip().lower()
            if conf_inst_id and inst_id and conf_inst_id == inst_id:
                declared_match = conflict
                break
            if conf_inst_name and inst_name and (conf_inst_name in inst_name or inst_name in conf_inst_name):
                declared_match = conflict
                break

        if declared_match:
            is_prohibited = True
            rules_checked.append({
                "rule_code": "DECLARED_CONFLICTS",
                "rule_name": "Declared Conflict Registry Verification",
                "status": "FAILED",
                "details": f"Expert declared voluntary conflict: {declared_match.get('reason', 'Declared personal conflict')}"
            })
        else:
            rules_checked.append({
                "rule_code": "DECLARED_CONFLICTS",
                "rule_name": "Declared Conflict Registry Verification",
                "status": "PASSED",
                "details": "No voluntary conflict declared for this institution."
            })

        # Rule 4: Cooling-Off Period (Default: 3 Years Illustrative Demonstration Policy)
        now = datetime.now(timezone.utc)
        cooling_off_cutoff = now - timedelta(days=cooling_off_years * 365)
        recent_visit = None

        for visit in (expert.prior_inspections or []):
            v_inst_id = visit.get("institution_id")
            v_inst_name = (visit.get("institution_name") or "").strip().lower()
            matches_inst = (v_inst_id and inst_id and v_inst_id == inst_id) or (v_inst_name and inst_name and v_inst_name in inst_name)

            if matches_inst:
                v_date_str = visit.get("inspection_date")
                if v_date_str:
                    try:
                        v_date = datetime.fromisoformat(v_date_str).replace(tzinfo=timezone.utc)
                    except Exception:
                        try:
                            v_date = datetime.strptime(v_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        except Exception:
                            v_date = now
                    if v_date >= cooling_off_cutoff:
                        recent_visit = visit
                        break

        if recent_visit:
            is_prohibited = True
            rules_checked.append({
                "rule_code": "COOLING_OFF_PERIOD",
                "rule_name": f"Prior Inspection Cooling-Off Period ({cooling_off_years} Years Demonstration Policy)",
                "status": "FAILED",
                "details": f"Expert previously inspected this institution on {recent_visit.get('inspection_date')} (cooling-off requires {cooling_off_years} years)."
            })
        else:
            rules_checked.append({
                "rule_code": "COOLING_OFF_PERIOD",
                "rule_name": f"Prior Inspection Cooling-Off Period ({cooling_off_years} Years Demonstration Policy)",
                "status": "PASSED",
                "details": f"No prior inspection of this institution within the {cooling_off_years}-year cooling-off window."
            })

        # Rule 5: Operational Availability
        if not expert.is_active or expert.availability_status != "AVAILABLE":
            is_prohibited = True
            rules_checked.append({
                "rule_code": "EXPERT_AVAILABILITY",
                "rule_name": "Expert Registry Availability Status",
                "status": "FAILED",
                "details": f"Expert status is '{expert.availability_status}' (active={expert.is_active})."
            })
        else:
            rules_checked.append({
                "rule_code": "EXPERT_AVAILABILITY",
                "rule_name": "Expert Registry Availability Status",
                "status": "PASSED",
                "details": "Expert is active and marked available for EVC assignments."
            })

        summary_msg = (
            "Conflict of Interest detected: Proposed assignment violates configured regulatory norms."
            if is_prohibited else
            "All Conflict-of-Interest rules PASSED. Expert is eligible for appointment."
        )

        return {
            "expert_id": expert.id,
            "expert_name": expert.name,
            "current_institution": expert.current_institution,
            "is_prohibited": is_prohibited,
            "can_override": is_prohibited,  # Overrides permissible with authorized role and mandatory audit reason
            "summary": summary_msg,
            "rules_checked": rules_checked,
            "assessed_at": now.isoformat(),
            "data_completeness": "COMPLETE"
        }


class EVCWorkflowService:
    """
    Orchestrates the structured expert invitation lifecycle and field inspection evidence.
    """

    @classmethod
    def propose_panel_assignment(
        cls,
        db: Session,
        inspection_id: int,
        expert_id: int,
        panel_role: str,
        actor: User,
        override_reason: Optional[str] = None
    ) -> EVCPanelAssignment:
        inspection = db.query(EVCInspection).filter(EVCInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="EVC Inspection record not found")

        expert = db.query(EVCExpert).filter(EVCExpert.id == expert_id).first()
        if not expert:
            raise HTTPException(status_code=404, detail=f"EVC Expert #{expert_id} not found in registry")

        # Regional scope check
        if inspection.application and inspection.application.institution:
            check_regional_scope(actor, inspection.application.institution.region)

        # Permission check
        if not has_permission(actor, Permission.EVC_SCHEDULE):
            raise HTTPException(status_code=403, detail="Unauthorized: User does not hold 'evc.schedule' permission")

        # Run explainable COI check
        coi_assessment = EVCConflictService.evaluate_coi(expert, inspection.application)

        override_applied = False
        if coi_assessment["is_prohibited"]:
            # Strict permission boundary: EVC_SCHEDULE does not imply EVC_COI_OVERRIDE
            if not has_permission(actor, Permission.EVC_COI_OVERRIDE):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "Proposed assignment blocked by Conflict-of-Interest policy. Actor does not hold 'evc.coi_override' permission.",
                        "coi_assessment": coi_assessment,
                        "override_required": True
                    }
                )
            if not override_reason or len(override_reason.strip()) < 15:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Proposed assignment blocked by Conflict-of-Interest policy. Substantive written justification (minimum 15 characters) is required to override regulatory conflict-of-interest findings.",
                        "coi_assessment": coi_assessment,
                        "override_required": True
                    }
                )
            # Override applied with verified authorization and substantive justification
            override_applied = True
            failed_rules = [r["rule_code"] for r in coi_assessment.get("rules_checked", []) if r.get("status") == "FAILED"]
            now_override = datetime.now(timezone.utc)
            log_audit_event(
                db=db,
                action="EVC_COI_OVERRIDE_APPLIED",
                entity_type="EVC",
                entity_id=inspection.id,
                actor_id=actor.id,
                actor_name=actor.full_name,
                actor_role=actor.roles[0].role if actor.roles else "EVC_COORDINATOR",
                details={
                    "expert_id": expert.id,
                    "expert_name": expert.name,
                    "panel_role": panel_role,
                    "overridden_rules": failed_rules,
                    "override_reason": override_reason.strip(),
                    "coi_assessment": coi_assessment,
                    "timestamp": now_override.isoformat()
                }
            )

        # Check existing assignment for this expert on this inspection
        existing = db.query(EVCPanelAssignment).filter(
            EVCPanelAssignment.inspection_id == inspection.id,
            EVCPanelAssignment.expert_id == expert.id,
            EVCPanelAssignment.status.in_(["PROPOSED", "INVITED", "ACCEPTED"])
        ).first()

        if existing:
            return existing

        now = datetime.now(timezone.utc)
        assignment = EVCPanelAssignment(
            inspection_id=inspection.id,
            expert_id=expert.id,
            panel_role=panel_role,
            status="PROPOSED",
            coi_check_result=coi_assessment,
            override_applied=override_applied,
            override_reason=override_reason.strip() if override_reason else None,
            override_by_id=actor.id if override_applied else None,
            override_at=now if override_applied else None,
            created_at=now,
            updated_at=now
        )
        db.add(assignment)
        inspection.panel_status = "PENDING_PANEL"
        db.commit()
        db.refresh(assignment)
        return assignment

    @classmethod
    def invite_expert(
        cls,
        db: Session,
        assignment_id: int,
        actor: User
    ) -> EVCPanelAssignment:
        assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Panel assignment not found")

        if not has_permission(actor, Permission.EVC_SCHEDULE):
            raise HTTPException(status_code=403, detail="Unauthorized to dispatch EVC panel invitations")

        now = datetime.now(timezone.utc)
        assignment.status = "INVITED"
        assignment.invited_at = now
        assignment.updated_at = now

        inspection = assignment.inspection
        inspection.panel_status = "INVITATIONS_DISPATCHED"

        # Enqueue transactional outbox invitation
        expert = assignment.expert
        app = inspection.application
        OutboxDispatcherService.queue_notification(
            db=db,
            event_type="EVC_EXPERT_INVITATION",
            entity_type="EVC",
            entity_id=inspection.id,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            params={
                "subject": f"AICTE EVC Panel Invitation: {inspection.inspection_type} Inspection",
                "message": f"You have been invited as {assignment.panel_role} for application {app.application_number if app else 'Case'}.",
                "link_url": f"/evc/assignments/{assignment.id}/respond"
            },
            institution_id=app.institution_id if app else None,
            region=inspection.application.institution.region if (app and app.institution) else None,
            recipient_role="COMMITTEE_MEMBER",
            recipient_user_id=expert.user_id,
            recipient_email=expert.email
        )

        db.commit()
        db.refresh(assignment)
        return assignment

    @classmethod
    def accept_invitation(
        cls,
        db: Session,
        assignment_id: int,
        actor: User
    ) -> EVCPanelAssignment:
        assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Panel assignment not found")

        # 1. State check: Must be in status "INVITED"
        if assignment.status != "INVITED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assignment #{assignment_id} is in status '{assignment.status}'. Only assignments in 'INVITED' status can be accepted."
            )

        expert = assignment.expert
        if not expert:
            raise HTTPException(status_code=404, detail="Assigned expert record not found")

        # 2. Account link check: Expert must be linked to an authenticated user account
        if expert.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Expert #{expert.id} ({expert.name}) is not linked to an active user account. Unlinked experts cannot accept invitations via API; an authorized coordinator must reassign or link the account."
            )

        # 3. User identity binding: Actor must be the explicitly linked expert user
        if expert.user_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only the invited expert linked to this assignment can accept this invitation. Responding on behalf of another expert is strictly prohibited."
            )

        now = datetime.now(timezone.utc)
        assignment.status = "ACCEPTED"
        assignment.responded_at = now
        assignment.updated_at = now

        inspection = assignment.inspection

        # Sync inspection legacy convener/expert columns for backward compatibility
        if assignment.panel_role == "CONVENER":
            inspection.convener_name = f"{expert.name} ({expert.current_institution})"
            inspection.convener_user_id = expert.user_id
        elif assignment.panel_role == "EXPERT_MEMBER":
            inspection.expert_member_name = f"{expert.name} ({expert.current_institution})"
            inspection.expert_user_id = expert.user_id

        # Check if panel is complete (at least one Convener and one Expert Member accepted)
        all_assignments = db.query(EVCPanelAssignment).filter(
            EVCPanelAssignment.inspection_id == inspection.id
        ).all()
        accepted_roles = {a.panel_role for a in all_assignments if a.status == "ACCEPTED"}
        if "CONVENER" in accepted_roles and "EXPERT_MEMBER" in accepted_roles:
            inspection.panel_status = "PANEL_CONFIRMED"
            if inspection.status == "PENDING_ASSIGNMENT":
                inspection.status = "SCHEDULED"

        actor_role = actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER"
        log_audit_event(
            db=db,
            action="EVC_INVITATION_ACCEPTED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "assignment_id": assignment.id,
                "expert_id": expert.id,
                "expert_name": expert.name,
                "panel_role": assignment.panel_role,
                "panel_status": inspection.panel_status
            }
        )

        db.commit()
        db.refresh(assignment)
        return assignment

    @classmethod
    def decline_invitation(
        cls,
        db: Session,
        assignment_id: int,
        reason: str,
        actor: User
    ) -> EVCPanelAssignment:
        assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Panel assignment not found")

        # 1. State check: Must be in status "INVITED"
        if assignment.status != "INVITED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assignment #{assignment_id} is in status '{assignment.status}'. Only assignments in 'INVITED' status can be declined."
            )

        expert = assignment.expert
        if not expert:
            raise HTTPException(status_code=404, detail="Assigned expert record not found")

        # 2. Account link check
        if expert.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Expert #{expert.id} ({expert.name}) is not linked to an active user account. Unlinked experts cannot decline invitations via API; an authorized coordinator must reassign or link the account."
            )

        # 3. User identity binding
        if expert.user_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only the invited expert linked to this assignment can decline this invitation. Responding on behalf of another expert is strictly prohibited."
            )

        # 4. Mandatory substantive reason check (minimum 5 chars)
        clean_reason = (reason or "").strip()
        if len(clean_reason) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decline reason is mandatory and must be substantive (at least 5 characters)."
            )

        now = datetime.now(timezone.utc)
        assignment.status = "DECLINED"
        assignment.responded_at = now
        assignment.decline_reason = clean_reason
        assignment.updated_at = now

        # Invariant: A declined invitation must return to the authorized coordinator for reassignment.
        # It must NOT silently remain an accepted panel member.
        inspection = assignment.inspection
        inspection.panel_status = "REASSIGNMENT_REQUIRED"

        # Clear legacy fields if this was the convener/expert
        if assignment.panel_role == "CONVENER" and inspection.convener_user_id == assignment.expert.user_id:
            inspection.convener_name = None
            inspection.convener_user_id = None
        elif assignment.panel_role == "EXPERT_MEMBER" and inspection.expert_user_id == assignment.expert.user_id:
            inspection.expert_member_name = None
            inspection.expert_user_id = None

        actor_role = actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER"
        log_audit_event(
            db=db,
            action="EVC_INVITATION_DECLINED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "assignment_id": assignment.id,
                "expert_id": assignment.expert.id,
                "expert_name": assignment.expert.name,
                "panel_role": assignment.panel_role,
                "decline_reason": assignment.decline_reason,
                "inspection_status": inspection.status
            }
        )

        db.commit()
        db.refresh(assignment)
        return assignment

    @classmethod
    def reassign_panel_member(
        cls,
        db: Session,
        old_assignment_id: int,
        new_expert_id: int,
        actor: User,
        override_reason: Optional[str] = None
    ) -> EVCPanelAssignment:
        old_assignment = db.query(EVCPanelAssignment).filter(EVCPanelAssignment.id == old_assignment_id).first()
        if not old_assignment:
            raise HTTPException(status_code=404, detail="Original panel assignment not found")

        # Regional scope check on inspection
        inspection = old_assignment.inspection
        if inspection and inspection.application and inspection.application.institution:
            check_regional_scope(actor, inspection.application.institution.region)

        # Propose replacement expert FIRST to preserve consistency on failure
        new_assignment = cls.propose_panel_assignment(
            db=db,
            inspection_id=old_assignment.inspection_id,
            expert_id=new_expert_id,
            panel_role=old_assignment.panel_role,
            actor=actor,
            override_reason=override_reason
        )

        # Only mutate old assignment after new proposal succeeds
        old_assignment.status = "REASSIGNED"
        old_assignment.updated_at = datetime.now(timezone.utc)

        actor_role = actor.roles[0].role if actor.roles else "EVC_COORDINATOR"
        log_audit_event(
            db=db,
            action="EVC_PANEL_MEMBER_REASSIGNED",
            entity_type="EVC",
            entity_id=old_assignment.inspection_id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "previous_assignment_id": old_assignment.id,
                "previous_expert_id": old_assignment.expert_id,
                "new_expert_id": new_expert_id,
                "new_assignment_id": new_assignment.id,
                "panel_role": old_assignment.panel_role
            }
        )

        db.commit()
        db.refresh(old_assignment)
        return new_assignment

    @classmethod
    def check_in_inspection(
        cls,
        db: Session,
        inspection_id: int,
        latitude: Optional[float],
        longitude: Optional[float],
        accuracy: Optional[float],
        source: Optional[str],
        actor: User
    ) -> EVCInspection:
        """
        Records inspector field check-in with transparent location accuracy provenance.
        Coordinates are recorded without falsely claiming spoof-proof certainty.
        """
        inspection = db.query(EVCInspection).filter(EVCInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="EVC Inspection not found")

        # Regional scope check
        if inspection.application and inspection.application.institution:
            check_regional_scope(actor, inspection.application.institution.region)

        # Coordinate bounds and accuracy validation
        if latitude is not None:
            if latitude < -90.0 or latitude > 90.0:
                raise HTTPException(status_code=400, detail="Invalid GPS latitude. Must be between -90 and 90 degrees.")
            if longitude is not None and (longitude < -180.0 or longitude > 180.0):
                raise HTTPException(status_code=400, detail="Invalid GPS longitude. Must be between -180 and 180 degrees.")
            if accuracy is not None and accuracy < 0:
                raise HTTPException(status_code=400, detail="Invalid GPS accuracy. Must be non-negative.")

        now = datetime.now(timezone.utc)
        inspection.check_in_at = now
        inspection.check_in_lat = latitude
        inspection.check_in_lon = longitude
        inspection.check_in_accuracy = accuracy
        inspection.check_in_source = source or ("BROWSER_GEOLOCATION" if latitude else "MANUAL_OFFICER_OVERRIDE")
        inspection.status = "IN_PROGRESS"

        actor_role = actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER"
        log_audit_event(
            db=db,
            action="EVC_INSPECTION_CHECKED_IN",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor_role,
            details={
                "check_in_time": now.isoformat(),
                "latitude": latitude,
                "longitude": longitude,
                "accuracy_meters": accuracy,
                "source": inspection.check_in_source
            }
        )

        db.commit()
        db.refresh(inspection)
        return inspection

    @classmethod
    def record_field_evidence(
        cls,
        db: Session,
        inspection_id: int,
        checklist_item_code: str,
        requirement_title: str,
        observation_notes: str,
        status: str,
        file_url: Optional[str],
        file_content: Optional[bytes],
        file_name: Optional[str],
        evidence_type: str,
        latitude: Optional[float],
        longitude: Optional[float],
        accuracy: Optional[float],
        source: Optional[str],
        permission_granted: bool,
        actor: User
    ) -> EVCFieldEvidence:
        inspection = db.query(EVCInspection).filter(EVCInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="EVC Inspection not found")

        # Regional scope check
        if inspection.application and inspection.application.institution:
            check_regional_scope(actor, inspection.application.institution.region)

        # Validate that client-supplied file_url references registered, authorized platform storage
        if file_url:
            ALLOWED_STORAGE_PREFIXES = ("/storage/", "/api/documents/download/", "https://storage.aicte.gov.in/", "/uploads/")
            if not any(file_url.startswith(prefix) for prefix in ALLOWED_STORAGE_PREFIXES):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid evidence file_url: Evidence must point to a registered, authorized platform storage endpoint."
                )

        # Compute SHA-256 hash
        file_hash = None
        file_size = None
        if file_content:
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
        elif file_url:
            file_hash = hashlib.sha256(file_url.encode("utf-8")).hexdigest()
            file_size = len(file_url.encode("utf-8"))
        elif observation_notes:
            file_hash = hashlib.sha256(f"{checklist_item_code}:{observation_notes}".encode("utf-8")).hexdigest()
            file_size = len(observation_notes.encode("utf-8"))

        now = datetime.now(timezone.utc)
        evidence = EVCFieldEvidence(
            inspection_id=inspection.id,
            checklist_item_code=checklist_item_code,
            requirement_title=requirement_title,
            observation_notes=observation_notes,
            status=status,
            file_url=file_url,
            file_hash=file_hash,
            file_name=file_name,
            file_size_bytes=file_size,
            evidence_type=evidence_type,
            captured_by_id=actor.id,
            captured_at=now,
            latitude=latitude,
            longitude=longitude,
            location_accuracy_meters=accuracy,
            location_capture_source=source or ("BROWSER_GEOLOCATION" if latitude else "MANUAL_OFFICER_OVERRIDE"),
            location_permission_granted=permission_granted,
            created_at=now,
            updated_at=now
        )
        db.add(evidence)

        actor_role = actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER"
        log_audit_event(
            db=db,
            action="EVC_FIELD_EVIDENCE_RECORDED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER",
            details={
                "checklist_item_code": checklist_item_code,
                "status": status,
                "file_hash": file_hash,
                "location_permission_granted": permission_granted
            }
        )

        db.commit()
        db.refresh(evidence)
        return evidence

    @classmethod
    def finalize_inspection_report(
        cls,
        db: Session,
        inspection_id: int,
        report_url: str,
        report_notes: str,
        recommendation: str,
        virtual_meeting_url: Optional[str],
        virtual_recording_url: Optional[str],
        actor: User
    ) -> EVCInspection:
        """
        Submits field inspection evidence and professional observations.
        Statutory Safeguard:
        - Inspection recommendation moves application ONLY to prescribed next stage (e.g. EVC_COMPLETED).
        - NEVER grants final statutory approval or rejection.
        - Competent Authority exclusively retains final decision order authority.
        """
        inspection = db.query(EVCInspection).filter(EVCInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="EVC Inspection not found")

        if not has_permission(actor, Permission.EVC_REPORT):
            raise HTTPException(status_code=403, detail="Unauthorized: User does not hold 'evc.report' permission")

        valid_recs = {"RECOMMENDED_APPROVAL", "RECOMMENDED_REJECTION", "DEFICIENCY_NOTED"}
        if recommendation not in valid_recs:
            raise HTTPException(status_code=400, detail=f"Invalid recommendation '{recommendation}'. Must be one of {valid_recs}")

        now = datetime.now(timezone.utc)
        inspection.report_url = report_url
        inspection.report_notes = report_notes
        inspection.recommendation = recommendation
        inspection.completed_at = now
        inspection.completed_by_id = actor.id
        inspection.status = "REPORT_SUBMITTED"

        if virtual_meeting_url:
            inspection.virtual_meeting_url = virtual_meeting_url
        if virtual_recording_url:
            inspection.virtual_recording_url = virtual_recording_url

        # Transition application to EVC_COMPLETED
        app = inspection.application
        if app and app.current_stage in ["EVC_SCHEDULED", "AWAITING_EVC_SCHEDULE"]:
            execute_transition(
                db=db,
                application=app,
                to_stage="EVC_COMPLETED",
                actor=actor,
                remarks=f"EVC Inspection Completed. Recommendation: {recommendation}. Report: {report_url or 'Dossier Filed'}."
            )

        log_audit_event(
            db=db,
            action="EVC_REPORT_SUBMITTED",
            entity_type="EVC",
            entity_id=inspection.id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            actor_role=actor.roles[0].role if actor.roles else "COMMITTEE_MEMBER",
            details={
                "recommendation": recommendation,
                "report_url": report_url,
                "notes_length": len(report_notes or ""),
                "has_virtual_recording": bool(virtual_recording_url)
            }
        )

        db.commit()
        db.refresh(inspection)
        return inspection

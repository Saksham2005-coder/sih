import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.rule import RuleDefinition, RuleVersionHistory
from app.models.application import Application
from app.schemas.rule import (
    RuleDefinitionResponse, RuleDefinitionUpdate, RuleVersionHistoryResponse,
    RuleValidateRequest, RuleValidateResponse, RuleSimulateRequest,
    RuleSimulateResponse, RulePublishRequest
)
from app.services.audit_service import log_audit_event
from app.services.priority_service import calculate_priority

router = APIRouter(prefix="/rules", tags=["Rule Studio"])

CANONICAL_ROLES = {
    "INSTITUTION_ADMIN", "COMPLIANCE_OFFICER", "REGIONAL_OFFICER",
    "BUREAU_OFFICER", "COMMITTEE_MEMBER", "EVC_COORDINATOR",
    "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
}

CANONICAL_ESCALATION_TIERS = {
    "REMINDER_L1", "REMINDER_L2", "ESCALATION_L1_RO", "ESCALATION_L2_BO", "ESCALATION_L3_MEMBER_SEC"
}

def validate_rule_config(rule_code: str, config_json_str: str) -> tuple[bool, List[str], List[str]]:
    """Validates configuration parameters against schema and operational constraints."""
    errors: List[str] = []
    warnings: List[str] = []

    try:
        cfg = json.loads(config_json_str)
    except Exception as e:
        return False, [f"Invalid JSON syntax: {str(e)}"], []

    if not isinstance(cfg, dict):
        return False, ["Rule configuration root must be a JSON object"], []

    # 1. Scrutiny / SLA Rules
    if "sla_days" in cfg:
        if not isinstance(cfg["sla_days"], int) or cfg["sla_days"] <= 0:
            errors.append("Field 'sla_days' must be a positive integer greater than 0")
        if "escalation_target" in cfg and cfg["escalation_target"] not in CANONICAL_ROLES:
            errors.append(f"Invalid escalation_target '{cfg['escalation_target']}'. Must be one of {sorted(list(CANONICAL_ROLES))}")

    # 2. Cure Window Rules
    if "cure_window_days" in cfg:
        if not isinstance(cfg["cure_window_days"], int) or cfg["cure_window_days"] <= 0:
            errors.append("Field 'cure_window_days' must be a positive integer")
        if "grace_period_days" in cfg and (not isinstance(cfg["grace_period_days"], int) or cfg["grace_period_days"] < 0):
            errors.append("Field 'grace_period_days' must be a non-negative integer")

    # 3. Warning Thresholds / Offsets
    if "warning_threshold_days" in cfg:
        thresh = cfg["warning_threshold_days"]
        if not isinstance(thresh, list) or not all(isinstance(x, int) and x >= 0 for x in thresh):
            errors.append("Field 'warning_threshold_days' must be a list of non-negative integers")
        elif len(thresh) > 1 and thresh != sorted(thresh, reverse=True):
            warnings.append("Warning threshold days should ideally be arranged in descending order (e.g. [15, 7, 0])")

    # 4. Escalation Chain
    if "escalation_chain" in cfg:
        chain = cfg["escalation_chain"]
        if not isinstance(chain, list) or len(chain) == 0:
            errors.append("Field 'escalation_chain' must be a non-empty list of tier definitions")
        else:
            prev_overdue = -1
            for idx, step in enumerate(chain):
                if not isinstance(step, dict):
                    errors.append(f"Escalation chain step #{idx+1} must be a JSON object")
                    continue
                tier = step.get("tier")
                target_role = step.get("target_role")
                min_overdue = step.get("min_overdue_days")

                if tier not in CANONICAL_ESCALATION_TIERS:
                    errors.append(f"Step #{idx+1}: invalid escalation tier '{tier}'. Must be one of {sorted(list(CANONICAL_ESCALATION_TIERS))}")
                if target_role not in CANONICAL_ROLES:
                    errors.append(f"Step #{idx+1}: invalid target_role '{target_role}'. Must be a canonical role")
                if not isinstance(min_overdue, int) or min_overdue < 0:
                    errors.append(f"Step #{idx+1}: 'min_overdue_days' must be an integer >= 0")
                elif min_overdue <= prev_overdue:
                    errors.append(f"Step #{idx+1}: 'min_overdue_days' ({min_overdue}) must strictly exceed preceding step ({prev_overdue})")
                if isinstance(min_overdue, int):
                    prev_overdue = min_overdue

    # 5. Priority Policy Weights
    if "weights" in cfg:
        weights = cfg["weights"]
        if not isinstance(weights, dict):
            errors.append("Field 'weights' must be a JSON object of numeric priority weights")
        else:
            for k, v in weights.items():
                if not isinstance(v, (int, float)) or v < 0 or v > 100:
                    errors.append(f"Priority weight '{k}' must be a numeric value between 0 and 100")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


@router.get("", response_model=List[RuleDefinitionResponse])
def list_rules(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all configured regulatory rule definitions."""
    query = db.query(RuleDefinition)
    if category:
        query = query.filter(RuleDefinition.category == category)
    return query.order_by(RuleDefinition.category.asc(), RuleDefinition.rule_code.asc()).all()


@router.get("/{rule_code}", response_model=RuleDefinitionResponse)
def get_rule_detail(
    rule_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch detailed definition for a single rule code."""
    rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule definition '{rule_code}' not found")
    return rule


@router.get("/{rule_code}/history", response_model=List[RuleVersionHistoryResponse])
def get_rule_version_history(
    rule_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List immutable previous version snapshots for a rule code."""
    history = db.query(RuleVersionHistory).filter(
        RuleVersionHistory.rule_code == rule_code
    ).order_by(RuleVersionHistory.created_at.desc()).all()
    return history


@router.post("/{rule_code}/validate", response_model=RuleValidateResponse)
def validate_rule(
    rule_code: str,
    payload: RuleValidateRequest,
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER"]))
):
    """Validate candidate rule configuration syntax, schema, and threshold semantics."""
    is_valid, errors, warnings = validate_rule_config(rule_code, payload.config_json)
    return RuleValidateResponse(
        valid=is_valid,
        errors=errors,
        warnings=warnings
    )


@router.post("/{rule_code}/simulate", response_model=RuleSimulateResponse)
def simulate_rule(
    rule_code: str,
    payload: RuleSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER"]))
):
    """Simulate rule outcomes against test scenarios or a real case WITHOUT mutating state or sending alerts."""
    rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule definition not found")

    cfg_str = payload.config_json or rule.config_json
    is_valid, errors, _ = validate_rule_config(rule_code, cfg_str)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Cannot simulate invalid configuration: {'; '.join(errors)}")

    cfg = json.loads(cfg_str)
    sim_results: Dict[str, Any] = {}

    if rule.category == "PRIORITY" or "weights" in cfg:
        # Simulate priority scoring
        if payload.application_id:
            app = db.query(Application).filter(Application.id == payload.application_id).first()
            if not app:
                raise HTTPException(status_code=404, detail="Test application not found")
            score, factors = calculate_priority(app, db)
            sim_results["application_number"] = app.application_number
            sim_results["evaluated_score"] = score
            sim_results["evaluated_tier"] = factors["tier"]
            sim_results["factors"] = factors["factors"]
            sim_results["recommended_action"] = factors["recommended_action"]
        else:
            sim_results["hypothetical_score"] = 65
            sim_results["hypothetical_tier"] = "High"
            sim_results["simulated_factors"] = [
                "Stage pendency > 7 days (+20 pts)",
                "Open deficiencies: 2 items (+20 pts)",
                "Active cure window (+15 pts)",
                "Baseline weight (+10 pts)"
            ]
    elif "escalation_chain" in cfg or rule.category == "ESCALATION":
        chain = cfg.get("escalation_chain", [])
        sim_results["predicted_escalation_steps"] = [
            {
                "trigger_at_overdue_day": step.get("min_overdue_days"),
                "tier": step.get("tier"),
                "recipient_role": step.get("target_role"),
                "idempotent_key_preview": f"{rule_code}:SAMPLE:{step.get('tier')}"
            }
            for step in chain
        ]
    elif "sla_days" in cfg or "cure_window_days" in cfg:
        sla = cfg.get("sla_days", cfg.get("cure_window_days", 7))
        sim_results["sla_threshold_days"] = sla
        sim_results["reminder_offsets"] = [f"T-{sla} (Submission)", f"T-3 (Warning)", f"T-0 (Deadline)"]
        sim_results["escalation_target"] = cfg.get("escalation_target", "REGIONAL_OFFICER")

    return RuleSimulateResponse(
        rule_code=rule_code,
        version=rule.version,
        simulation_results=sim_results
    )


@router.post("/{rule_code}/publish", response_model=RuleDefinitionResponse)
def publish_rule_version(
    rule_code: str,
    payload: RulePublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))
):
    """Publishes a new validated version of a regulatory rule, archiving previous configuration in history."""
    rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule definition not found")

    is_valid, errors, _ = validate_rule_config(rule_code, payload.config_json)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Cannot publish invalid configuration: {'; '.join(errors)}")

    # 1. Archive prior version into history
    history_entry = RuleVersionHistory(
        rule_id=rule.id,
        rule_code=rule.rule_code,
        version=rule.version,
        category=rule.category,
        config_json=rule.config_json,
        status="RETIRED",
        change_reason=rule.change_reason or "Superseded by new version publish",
        created_by_id=current_user.id
    )
    db.add(history_entry)

    # 2. Update active rule
    old_version = rule.version
    rule.version = payload.version
    rule.config_json = payload.config_json
    rule.status = "PUBLISHED"
    rule.is_active = True
    rule.change_reason = payload.change_reason
    rule.created_by_id = current_user.id
    rule.effective_from = datetime.now(timezone.utc)

    # 3. Audit trail
    log_audit_event(
        db=db,
        action="RULE_PUBLISHED",
        entity_type="RULE",
        entity_id=rule.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="SYSTEM_ADMIN",
        details={
            "rule_code": rule.rule_code,
            "old_version": old_version,
            "new_version": payload.version,
            "change_reason": payload.change_reason
        }
    )

    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_code}", response_model=RuleDefinitionResponse)
def update_rule(
    rule_code: str,
    request: RuleDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))
):
    """Update rule configuration parameters (auto-validates JSON syntax)."""
    rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule definition not found")

    is_valid, errors, _ = validate_rule_config(rule_code, request.config_json)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation failed: {'; '.join(errors)}")

    old_config = rule.config_json
    rule.config_json = request.config_json
    if request.version:
        rule.version = request.version
    if request.is_active is not None:
        rule.is_active = request.is_active
    if request.status:
        rule.status = request.status
    if request.description:
        rule.description = request.description
    if request.change_reason:
        rule.change_reason = request.change_reason

    log_audit_event(
        db=db,
        action="RULE_UPDATED",
        entity_type="RULE",
        entity_id=rule.id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role="SYSTEM_ADMIN",
        details={"rule_code": rule.rule_code, "old_config": old_config, "new_config": request.config_json}
    )

    db.commit()
    db.refresh(rule)
    return rule

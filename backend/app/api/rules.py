from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.rule import RuleDefinition
from app.schemas.rule import RuleDefinitionResponse, RuleDefinitionUpdate
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/rules", tags=["Rule Studio"])

@router.get("", response_model=List[RuleDefinitionResponse])
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(RuleDefinition).order_by(RuleDefinition.category.asc()).all()

@router.put("/{rule_code}", response_model=RuleDefinitionResponse)
def update_rule(
    rule_code: str,
    request: RuleDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))
):
    rule = db.query(RuleDefinition).filter(RuleDefinition.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule definition not found")

    old_config = rule.config_json
    rule.config_json = request.config_json
    if request.version:
        rule.version = request.version
    if request.is_active is not None:
        rule.is_active = request.is_active

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

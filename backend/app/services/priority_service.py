from datetime import datetime, timezone
import json
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.application import Application, Deficiency
from app.models.compliance import ComplianceUndertaking

def calculate_priority(application: Application, db: Session) -> Tuple[int, Dict[str, Any]]:
    score = 20 # Baseline priority
    factors = []
    
    # Factor 1: Ageing in current stage
    now = datetime.now(timezone.utc)
    app_updated_at = application.updated_at
    if app_updated_at.tzinfo is None:
        app_updated_at = app_updated_at.replace(tzinfo=timezone.utc)
    days_in_stage = (now - app_updated_at).days
    
    if days_in_stage > 14:
        score += 35
        factors.append(f"Severe case ageing: {days_in_stage} days in current stage '{application.current_stage}' (+35)")
    elif days_in_stage > 7:
        score += 20
        factors.append(f"Case ageing: {days_in_stage} days in current stage '{application.current_stage}' (+20)")
    elif days_in_stage > 3:
        score += 10
        factors.append(f"Moderate pendency: {days_in_stage} days in current stage (+10)")
    else:
        factors.append(f"Normal pendency: {days_in_stage} days in stage")

    # Factor 2: Open deficiencies
    open_defs = db.query(Deficiency).filter(
        Deficiency.application_id == application.id,
        Deficiency.status == "OPEN"
    ).count()
    if open_defs > 0:
        score += min(25, open_defs * 10)
        factors.append(f"Unresolved deficiencies: {open_defs} items pending resolution (+{min(25, open_defs * 10)})")

    # Factor 3: Application stage urgency
    if application.current_stage == "DEFICIENCY_COMMUNICATED":
        score += 15
        factors.append("Active deficiency cure window: High institutional urgency (+15)")
    elif application.current_stage == "AWAITING_EVC_SCHEDULE":
        score += 20
        factors.append("EVC Scheduling pending: Inspection panel unassigned (+20)")
    elif application.current_stage == "AWAITING_COMPETENT_AUTHORITY":
        score += 25
        factors.append("Final statutory approval milestone pending (+25)")

    # Factor 4: Associated compliance undertakings
    overdue_undertakings = db.query(ComplianceUndertaking).filter(
        ComplianceUndertaking.institution_id == application.institution_id,
        ComplianceUndertaking.status == "OVERDUE"
    ).count()
    if overdue_undertakings > 0:
        score += 15
        factors.append(f"Institution has {overdue_undertakings} overdue compliance undertakings (+15)")

    final_score = min(100, max(0, score))
    urgency_tier = "Low"
    if final_score >= 80:
        urgency_tier = "Critical"
    elif final_score >= 60:
        urgency_tier = "High"
    elif final_score >= 40:
        urgency_tier = "Medium"

    result = {
        "score": final_score,
        "tier": urgency_tier,
        "factors": factors,
        "calculated_at": now.isoformat()
    }
    return final_score, result

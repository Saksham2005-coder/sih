import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.alert import AlertEscalation
from app.models.rule import RuleDefinition

DEFAULT_PRIORITY_WEIGHTS = {
    "stage_ageing_severe": 35,
    "stage_ageing_high": 20,
    "stage_ageing_moderate": 10,
    "deficiency_item_weight": 10,
    "max_deficiency_points": 25,
    "stage_competent_authority": 25,
    "stage_evc_schedule": 20,
    "stage_deficiency_cure": 15,
    "stage_scrutiny": 10,
    "overdue_undertakings_weight": 15,
    "expiring_documents_weight": 10,
    "escalation_l2_weight": 20,
    "escalation_l3_weight": 30,
    "repeated_returns_weight": 15
}

def get_priority_policy(db: Session) -> Tuple[Dict[str, Any], str]:
    """Retrieves priority policy configuration from Rule Studio or defaults."""
    rule = db.query(RuleDefinition).filter(
        RuleDefinition.rule_code == "RULE_PRIORITY_POLICY",
        RuleDefinition.is_active == True
    ).first()
    if rule:
        try:
            cfg = json.loads(rule.config_json)
            weights = cfg.get("weights", DEFAULT_PRIORITY_WEIGHTS)
            return weights, rule.version
        except Exception:
            pass
    return DEFAULT_PRIORITY_WEIGHTS, "1.0.0"

def get_recommended_action(stage: str, open_deficiencies_count: int, evc_required: bool) -> str:
    """Deterministic recommendation for the next permitted regulatory step."""
    if stage == "AWAITING_COMPETENT_AUTHORITY":
        return "Review case dossier and record statutory concurrence / final decision."
    elif stage == "AWAITING_SAC_CAC_REVIEW":
        return "Convene SAC/CAC panel hearing and record formal committee minutes."
    elif stage == "EVC_COMPLETED":
        return "Verify submitted inspection findings and route to Committee review."
    elif stage == "EVC_SCHEDULED":
        return "Conduct scheduled inspection and upload committee visit report."
    elif stage == "AWAITING_EVC_SCHEDULE":
        return "Form inspection roster (convener + expert) and set inspection date."
    elif stage == "SCRUTINY_COMPLETED":
        return "Route to EVC queue or Committee Review based on approved template."
    elif stage == "DEFICIENCY_COMMUNICATED":
        return "Awaiting institutional cure documentation within active cure window."
    elif stage == "RESUBMITTED":
        return "Examine cured deficiencies and verify attached rectifications."
    elif stage == "UNDER_SCRUTINY":
        if open_deficiencies_count > 0:
            return "Resolve cured deficiencies or issue formal deficiency memo."
        return "Verify prerequisite documents and sign off scrutiny completion."
    elif stage == "SUBMITTED":
        return "Assign designated regional scrutiny officer to initiate review."
    elif stage in ("APPROVED", "REJECTED", "CLOSED"):
        return "Regulatory lifecycle completed. No operational actions pending."
    return "Perform stage-appropriate review in accordance with APH guidelines."

def calculate_priority(application: Application, db: Session) -> Tuple[int, Dict[str, Any]]:
    """Calculates deterministic Explainable Priority Score (0-100) and structured factors.
    Strict Invariant: Never mutates statutory decision state (APPROVED/REJECTED).
    """
    weights, policy_version = get_priority_policy(db)
    score = 15  # Calibrated baseline
    factors = []
    evidence_records = {}

    now = datetime.now(timezone.utc)
    app_updated_at = application.updated_at
    if app_updated_at.tzinfo is None:
        app_updated_at = app_updated_at.replace(tzinfo=timezone.utc)
    days_in_stage = max(0, (now - app_updated_at).days)

    # 1. Stage Ageing
    if days_in_stage > 14:
        pts = weights.get("stage_ageing_severe", 35)
        score += pts
        factors.append(f"Severe case ageing: {days_in_stage} days in current stage '{application.current_stage}' (+{pts} pts)")
    elif days_in_stage > 7:
        pts = weights.get("stage_ageing_high", 20)
        score += pts
        factors.append(f"High case pendency: {days_in_stage} days in current stage '{application.current_stage}' (+{pts} pts)")
    elif days_in_stage > 3:
        pts = weights.get("stage_ageing_moderate", 10)
        score += pts
        factors.append(f"Moderate stage pendency: {days_in_stage} days in current stage (+{pts} pts)")
    else:
        factors.append(f"Normal stage pendency: {days_in_stage} days in stage")

    # 2. Unresolved Open Deficiencies
    open_defs = db.query(Deficiency).filter(
        Deficiency.application_id == application.id,
        Deficiency.status == "OPEN"
    ).all()
    open_defs_count = len(open_defs)
    if open_defs_count > 0:
        pts = min(weights.get("max_deficiency_points", 25), open_defs_count * weights.get("deficiency_item_weight", 10))
        score += pts
        factors.append(f"Unresolved deficiencies: {open_defs_count} items awaiting cure (+{pts} pts)")
        evidence_records["open_deficiencies"] = [d.id for d in open_defs]

    # 3. Application Stage Criticality
    if application.current_stage == "AWAITING_COMPETENT_AUTHORITY":
        pts = weights.get("stage_competent_authority", 25)
        score += pts
        factors.append(f"Final statutory approval milestone pending (+{pts} pts)")
    elif application.current_stage == "AWAITING_EVC_SCHEDULE":
        pts = weights.get("stage_evc_schedule", 20)
        score += pts
        factors.append(f"EVC scheduling required: Panel unassigned (+{pts} pts)")
    elif application.current_stage == "DEFICIENCY_COMMUNICATED":
        pts = weights.get("stage_deficiency_cure", 15)
        score += pts
        factors.append(f"Deficiency cure window active (+{pts} pts)")
    elif application.current_stage in ("UNDER_SCRUTINY", "RESUBMITTED"):
        pts = weights.get("stage_scrutiny", 10)
        score += pts
        factors.append(f"Active scrutiny verification required (+{pts} pts)")

    # 4. Overdue Compliance Undertakings
    overdue_undertakings = db.query(ComplianceUndertaking).filter(
        ComplianceUndertaking.institution_id == application.institution_id,
        ComplianceUndertaking.status == "OVERDUE"
    ).all()
    if overdue_undertakings:
        pts = weights.get("overdue_undertakings_weight", 15)
        score += pts
        factors.append(f"Institutional compliance breach: {len(overdue_undertakings)} overdue undertakings (+{pts} pts)")
        evidence_records["overdue_undertakings"] = [u.id for u in overdue_undertakings]

    # 5. Expiring Statutory Documents
    expiring_docs = db.query(DocumentRecord).filter(
        DocumentRecord.institution_id == application.institution_id,
        DocumentRecord.status.in_(["EXPIRING_SOON", "EXPIRED"])
    ).all()
    if expiring_docs:
        pts = weights.get("expiring_documents_weight", 10)
        score += pts
        factors.append(f"Document validity alert: {len(expiring_docs)} documents expiring or expired (+{pts} pts)")
        evidence_records["expiring_documents"] = [d.id for d in expiring_docs]

    # 6. Active Escalations
    active_escalations = db.query(AlertEscalation).filter(
        AlertEscalation.entity_type == "APPLICATION",
        AlertEscalation.entity_id == application.id,
        AlertEscalation.status == "ACTIVE"
    ).all()
    has_l3 = any(e.escalation_level == "ESCALATION_L3_MEMBER_SEC" for e in active_escalations)
    has_l2 = any(e.escalation_level == "ESCALATION_L2_BO" for e in active_escalations)
    if has_l3:
        pts = weights.get("escalation_l3_weight", 30)
        score += pts
        factors.append(f"Apex Escalation Active: Case breached L3 SLA threshold (+{pts} pts)")
    elif has_l2:
        pts = weights.get("escalation_l2_weight", 20)
        score += pts
        factors.append(f"Bureau Escalation Active: Case breached L2 SLA threshold (+{pts} pts)")

    # 7. Repeated Deficiency Cycles / Returns
    returns_count = db.query(ApplicationStage).filter(
        ApplicationStage.application_id == application.id,
        ApplicationStage.to_stage == "DEFICIENCY_COMMUNICATED"
    ).count()
    if returns_count > 1:
        pts = weights.get("repeated_returns_weight", 15)
        score += pts
        factors.append(f"Repeated deficiency loops: Returned {returns_count} times (+{pts} pts)")

    # Cap score between 0 and 100
    final_score = min(100, max(0, score))

    if final_score >= 80:
        urgency_tier = "Critical"
    elif final_score >= 60:
        urgency_tier = "High"
    elif final_score >= 40:
        urgency_tier = "Medium"
    else:
        urgency_tier = "Low"

    recommended_action = get_recommended_action(
        application.current_stage,
        open_defs_count,
        application.evc_required
    )

    result = {
        "score": final_score,
        "tier": urgency_tier,
        "factors": factors,
        "recommended_action": recommended_action,
        "policy_version": policy_version,
        "evidence_records": evidence_records,
        "calculated_at": now.isoformat()
    }

    return final_score, result


class PriorityFactor:
    def __init__(self, name: str, points: int = 0):
        self.name = name
        self.points = points

    def __repr__(self):
        return f"<PriorityFactor {self.name} (+{self.points} pts)>"


class PriorityResult:
    def __init__(self, total_score: int, priority_level: str, factors: list, next_action: str, policy_version: str, evidence_records: dict):
        self.total_score = total_score
        self.priority_level = priority_level
        self.factors = factors
        self.next_action = next_action
        self.policy_version = policy_version
        self.evidence_records = evidence_records

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.total_score,
            "tier": self.priority_level,
            "factors": [f.name if isinstance(f, PriorityFactor) else str(f) for f in self.factors],
            "recommended_action": self.next_action,
            "policy_version": self.policy_version,
            "evidence_records": self.evidence_records
        }


class PriorityService:
    """Service facade for Explainable Priority scoring."""

    @staticmethod
    def calculate_priority(application: Application, db: Session) -> Tuple[int, Dict[str, Any]]:
        return calculate_priority(application, db)

    @staticmethod
    def calculate_case_priority(application: Application, db: Session) -> PriorityResult:
        score, data = calculate_priority(application, db)
        factor_objs = []
        for f in data.get("factors", []):
            pts = 0
            if "(+" in f and " pts)" in f:
                try:
                    pts = int(f.split("(+")[1].split(" pts)")[0])
                except Exception:
                    pts = 0
            factor_objs.append(PriorityFactor(name=f, points=pts))
        return PriorityResult(
            total_score=score,
            priority_level=data.get("tier", "Low"),
            factors=factor_objs,
            next_action=data.get("recommended_action", ""),
            policy_version=data.get("policy_version", "1.0.0"),
            evidence_records=data.get("evidence_records", {})
        )


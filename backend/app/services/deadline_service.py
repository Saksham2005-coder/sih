import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.application import Application, Deficiency
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.evc import EVCInspection
from app.models.alert import Notification, AlertEscalation
from app.models.user import User

def generate_idempotency_key(entity_type: str, entity_id: int, trigger_type: str, threshold_days: int, escalation_level: str, recipient_role: str) -> str:
    raw = f"{entity_type}:{entity_id}:{trigger_type}:{threshold_days}:{escalation_level}:{recipient_role}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def run_deadline_and_escalation_scan(db: Session) -> Dict[str, Any]:
    start_time = time.time()
    now = datetime.now(timezone.utc)
    
    scanned_entities = 0
    reminders_created = 0
    escalations_created = 0
    duplicates_prevented = 0

    # 1. Check Compliance Undertakings
    undertakings = db.query(ComplianceUndertaking).filter(
        ComplianceUndertaking.status.in_(["NOT_YET_DUE", "DUE_SOON", "OVERDUE", "PENDING_VERIFICATION"])
    ).all()

    for u in undertakings:
        scanned_entities += 1
        due = u.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
            
        days_remaining = (due - now).days
        
        # Approaching deadline (<= 15 days)
        if 0 <= days_remaining <= 15 and u.status == "NOT_YET_DUE":
            u.status = "DUE_SOON"
            key = generate_idempotency_key("UNDERTAKING", u.id, "DUE_SOON", 15, "REMINDER_L1", "COMPLIANCE_OFFICER")
            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
            if not exists:
                esc = AlertEscalation(
                    idempotency_key=key,
                    entity_type="UNDERTAKING",
                    entity_id=u.id,
                    trigger_type="DUE_SOON",
                    threshold_days=15,
                    escalation_level="REMINDER_L1",
                    recipient_role="COMPLIANCE_OFFICER",
                    status="ACTIVE"
                )
                db.add(esc)
                notif = Notification(
                    institution_id=u.institution_id,
                    title=f"Compliance Due Soon: {u.title}",
                    message=f"Mandatory compliance undertaking '{u.title}' is due in {days_remaining} days ({due.strftime('%d %b %Y')}). Please submit verification evidence.",
                    level="WARNING",
                    link_url="/compliance"
                )
                db.add(notif)
                reminders_created += 1
            else:
                duplicates_prevented += 1

        # Overdue deadline (< 0 days and not verified)
        elif days_remaining < 0 and u.status in ["NOT_YET_DUE", "DUE_SOON"]:
            u.status = "OVERDUE"
            key = generate_idempotency_key("UNDERTAKING", u.id, "SLA_OVERDUE", abs(days_remaining), "ESCALATION_L1_RO", "REGIONAL_OFFICER")
            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
            if not exists:
                esc = AlertEscalation(
                    idempotency_key=key,
                    entity_type="UNDERTAKING",
                    entity_id=u.id,
                    trigger_type="SLA_OVERDUE",
                    threshold_days=abs(days_remaining),
                    escalation_level="ESCALATION_L1_RO",
                    recipient_role="REGIONAL_OFFICER",
                    status="ACTIVE"
                )
                db.add(esc)
                notif = Notification(
                    institution_id=u.institution_id,
                    title=f"OVERDUE Compliance Alert: {u.title}",
                    message=f"Compliance undertaking '{u.title}' passed its deadline on {due.strftime('%d %b %Y')} and is now OVERDUE by {abs(days_remaining)} days. Escalated to Regional Officer.",
                    level="DANGER",
                    link_url="/compliance"
                )
                db.add(notif)
                escalations_created += 1
            else:
                duplicates_prevented += 1

    # 2. Check Document Validity & Expiry
    documents = db.query(DocumentRecord).filter(
        DocumentRecord.status.in_(["ACTIVE", "EXPIRING_SOON", "EXPIRED"])
    ).all()

    for doc in documents:
        if not doc.expiry_date:
            continue
        scanned_entities += 1
        
        # Convert date to datetime at midnight UTC
        exp_dt = datetime(doc.expiry_date.year, doc.expiry_date.month, doc.expiry_date.day, tzinfo=timezone.utc)
        days_to_expiry = (exp_dt - now).days

        if 0 <= days_to_expiry <= 60 and doc.status == "ACTIVE":
            doc.status = "EXPIRING_SOON"
            key = generate_idempotency_key("DOCUMENT", doc.id, "EXPIRY_WARNING", 60, "REMINDER_L1", "INSTITUTION_ADMIN")
            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
            if not exists:
                esc = AlertEscalation(
                    idempotency_key=key,
                    entity_type="DOCUMENT",
                    entity_id=doc.id,
                    trigger_type="EXPIRY_WARNING",
                    threshold_days=60,
                    escalation_level="REMINDER_L1",
                    recipient_role="INSTITUTION_ADMIN",
                    status="ACTIVE"
                )
                db.add(esc)
                notif = Notification(
                    institution_id=doc.institution_id,
                    title=f"Document Expiring Soon: {doc.title}",
                    message=f"Prescribed document '{doc.title}' ({doc.document_type}) expires on {doc.expiry_date.strftime('%d %b %Y')} ({days_to_expiry} days remaining). Please initiate renewal submission.",
                    level="WARNING",
                    link_url="/documents"
                )
                db.add(notif)
                reminders_created += 1
            else:
                duplicates_prevented += 1

        elif days_to_expiry < 0 and doc.status != "EXPIRED":
            doc.status = "EXPIRED"
            key = generate_idempotency_key("DOCUMENT", doc.id, "EXPIRED", abs(days_to_expiry), "ESCALATION_L1_RO", "REGIONAL_OFFICER")
            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
            if not exists:
                esc = AlertEscalation(
                    idempotency_key=key,
                    entity_type="DOCUMENT",
                    entity_id=doc.id,
                    trigger_type="EXPIRED",
                    threshold_days=abs(days_to_expiry),
                    escalation_level="ESCALATION_L1_RO",
                    recipient_role="REGIONAL_OFFICER",
                    status="ACTIVE"
                )
                db.add(esc)
                notif = Notification(
                    institution_id=doc.institution_id,
                    title=f"EXPIRED Document Alert: {doc.title}",
                    message=f"Document '{doc.title}' expired on {doc.expiry_date.strftime('%d %b %Y')}. Institutional compliance status flagged.",
                    level="DANGER",
                    link_url="/documents"
                )
                db.add(notif)
                escalations_created += 1
            else:
                duplicates_prevented += 1

    # 3. Check Application Stage SLAs
    applications = db.query(Application).filter(
        Application.current_stage.in_(["SUBMITTED", "DEFICIENCY_COMMUNICATED", "AWAITING_EVC_SCHEDULE"])
    ).all()

    for app in applications:
        scanned_entities += 1
        updated = app.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        days_in_stage = (now - updated).days

        # Deficiency cure SLA: 15 days
        if app.current_stage == "DEFICIENCY_COMMUNICATED" and days_in_stage >= 15:
            key = generate_idempotency_key("APPLICATION", app.id, "DEFICIENCY_OVERDUE", 15, "ESCALATION_L2_BO", "BUREAU_OFFICER")
            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
            if not exists:
                esc = AlertEscalation(
                    idempotency_key=key,
                    entity_type="APPLICATION",
                    entity_id=app.id,
                    trigger_type="DEFICIENCY_OVERDUE",
                    threshold_days=15,
                    escalation_level="ESCALATION_L2_BO",
                    recipient_role="BUREAU_OFFICER",
                    status="ACTIVE"
                )
                db.add(esc)
                notif = Notification(
                    institution_id=app.institution_id,
                    title=f"CRITICAL ESCALATION: Deficiency Cure SLA Breached for {app.application_number}",
                    message=f"Application {app.application_number} has exceeded the 15-day statutory deficiency cure window ({days_in_stage} days elapsed). Escalated to Bureau Officer.",
                    level="DANGER",
                    link_url=f"/applications/{app.id}"
                )
                db.add(notif)
                escalations_created += 1
            else:
                duplicates_prevented += 1

    db.commit()
    exec_time = (time.time() - start_time) * 1000.0
    return {
        "scanned_entities": scanned_entities,
        "reminders_created": reminders_created,
        "escalations_created": escalations_created,
        "duplicates_prevented": duplicates_prevented,
        "execution_time_ms": round(exec_time, 2)
    }

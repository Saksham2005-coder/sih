import hashlib
import time
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.application import Application, Deficiency
from app.models.compliance import ComplianceUndertaking
from app.models.document import DocumentRecord
from app.models.evc import EVCInspection
from app.models.alert import Notification, AlertEscalation, DeadlineEngineRun
from app.models.rule import RuleDefinition
from app.models.user import User, UserRole
from app.models.institution import Institution

def generate_idempotency_key(
    entity_type: str,
    entity_id: int,
    trigger_type: str,
    threshold_days: int,
    escalation_level: str,
    recipient_role: str,
    cycle_id: str = "1"
) -> str:
    """Generates a cycle-aware cryptographic hash for zero-duplicate alert enforcement."""
    raw = f"{entity_type}:{entity_id}:{trigger_type}:{threshold_days}:{escalation_level}:{recipient_role}:{cycle_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def get_rule_config(db: Session, rule_code: str, default_config: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """Retrieves rule configuration JSON from Rule Studio or returns sensible defaults."""
    rule = db.query(RuleDefinition).filter(
        RuleDefinition.rule_code == rule_code,
        RuleDefinition.is_active == True
    ).first()
    if rule:
        try:
            return json.loads(rule.config_json), rule.version
        except Exception:
            pass
    return default_config, "1.0.0"

class DeadlineService:
    @staticmethod
    def calculate_deadline_condition(due_date_or_dt: Any, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculates derived status without destructive modification of original record.
        Preserves calendar date semantics (Asia/Kolkata) and exact timestamp boundaries.
        """
        from datetime import date
        IST = timezone(timedelta(hours=5, minutes=30))
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Handle pure calendar date object
        if isinstance(due_date_or_dt, date) and not isinstance(due_date_or_dt, datetime):
            now_ist_date = now.astimezone(IST).date()
            if now_ist_date > due_date_or_dt:
                days_overdue = (now_ist_date - due_date_or_dt).days
                return {
                    "condition": "OVERDUE",
                    "days_remaining": -days_overdue,
                    "days_overdue": days_overdue
                }
            elif now_ist_date == due_date_or_dt:
                return {
                    "condition": "DUE_TODAY",
                    "days_remaining": 0,
                    "days_overdue": 0
                }
            else:
                days_remaining = (due_date_or_dt - now_ist_date).days
                condition = "DUE_SOON" if days_remaining <= 7 else "ON_TRACK"
                return {
                    "condition": condition,
                    "days_remaining": days_remaining,
                    "days_overdue": 0
                }

        # Handle timestamp datetime
        target_dt = due_date_or_dt
        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)

        diff = target_dt - now
        total_seconds = diff.total_seconds()

        if total_seconds < 0:
            days_overdue = max(1, abs(diff.days))
            condition = "OVERDUE"
            days_remaining = -days_overdue
        elif total_seconds == 0 or diff.days == 0 or (total_seconds <= 86400 and now.astimezone(IST).date() == target_dt.astimezone(IST).date()):
            condition = "DUE_TODAY"
            days_remaining = 0
            days_overdue = 0
        else:
            days_remaining = diff.days if diff.days > 0 else 1
            condition = "DUE_SOON" if days_remaining <= 7 else "ON_TRACK"
            days_overdue = 0

        return {
            "condition": condition,
            "days_remaining": days_remaining,
            "days_overdue": days_overdue
        }

    @staticmethod
    def dispatch_notification(
        db: Session,
        institution_id: Optional[int],
        user_id: Optional[int],
        recipient_role: Optional[str],
        entity_type: str,
        entity_id: int,
        title: str,
        message: str,
        level: str,
        link_url: Optional[str],
        channel: str = "IN_APP"
    ) -> Notification:
        """Creates durable notification and records transactional outbox dispatch."""
        from app.services.notification.outbox_dispatcher import OutboxDispatcherService
        from app.models.user import User

        recipient_email = None
        recipient_phone = None
        if user_id:
            u = db.query(User).filter(User.id == user_id).first()
            if u:
                recipient_email = u.email
                recipient_phone = getattr(u, "phone", None)
        elif institution_id:
            from app.models.institution import Institution
            inst = db.query(Institution).filter(Institution.id == institution_id).first()
            if inst:
                recipient_email = getattr(inst, "email", None) or f"admin@inst{inst.id}.edu.in"
                recipient_phone = getattr(inst, "contact_number", None) or f"+91987654{inst.id:04d}"

        # 1. Enqueue in-app notification in Outbox
        outbox = OutboxDispatcherService.queue_notification(
            db=db,
            event_type=f"{entity_type}_ALERT",
            entity_type=entity_type,
            entity_id=entity_id,
            channel=channel,
            template_code="SLA_WARNING" if "SLA" in title else "DEFICIENCY_COMMUNICATED",
            params={
                "subject": title,
                "message": message,
                "link_url": link_url,
                "institution_name": f"Institution #{institution_id}" if institution_id else "AICTE Authority",
                "app_num": f"APP-{entity_id:04d}",
                "summary": message,
                "deadline": "Immediate Action Required"
            },
            institution_id=institution_id,
            recipient_role=recipient_role,
            recipient_user_id=user_id,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            link_url=link_url,
            level=level
        )

        # Retrieve or create Notification object linked to outbox
        notif = db.query(Notification).filter(Notification.outbox_id == outbox.id).first()
        if not notif:
            notif = Notification(
                institution_id=institution_id,
                user_id=user_id,
                recipient_role=recipient_role,
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                message=message,
                channel=channel,
                delivery_channel=channel,
                delivery_status="DELIVERED",
                level=level,
                is_read=False,
                link_url=link_url,
                outbox_id=outbox.id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(notif)

        # Also queue external EMAIL outbox item for high-priority or warning notifications
        if level in ["WARNING", "DANGER"] and channel == "IN_APP" and recipient_email:
            from app.services.notification.auth_policy import build_canonical_recipient_id
            recip_id = build_canonical_recipient_id(recipient_user_id=user_id, recipient_email=recipient_email, recipient_role=recipient_role)
            email_idempotency = f"OUTBOX:{entity_type}:{entity_id}:EMAIL:{title[:30]}:{recip_id}"
            OutboxDispatcherService.queue_notification(
                db=db,
                event_type=f"{entity_type}_URGENT_NOTICE",
                entity_type=entity_type,
                entity_id=entity_id,
                channel="EMAIL",
                template_code="SLA_WARNING" if "SLA" in title else "DEFICIENCY_COMMUNICATED",
                params={
                    "subject": title,
                    "message": message,
                    "app_num": f"APP-{entity_id:04d}",
                    "institution_name": f"Institution #{institution_id}" if institution_id else "AICTE",
                    "summary": message,
                    "deadline": "Immediate Compliance Required",
                    "link_url": link_url
                },
                institution_id=institution_id,
                recipient_role=recipient_role,
                recipient_user_id=user_id,
                recipient_email=recipient_email,
                idempotency_key=email_idempotency,
                link_url=link_url,
                level=level
            )

        return notif

    @staticmethod
    def auto_resolve_obsolete_escalations(
        db: Session,
        entity_type: str,
        entity_id: int,
        resolved_reason: str
    ) -> int:
        """Transitions active escalations to RESOLVED when the underlying matter is cured or verified."""
        active_escalations = db.query(AlertEscalation).filter(
            AlertEscalation.entity_type == entity_type,
            AlertEscalation.entity_id == entity_id,
            AlertEscalation.status.in_(["ACTIVE", "ACKNOWLEDGED"])
        ).all()

        count = 0
        now = datetime.now(timezone.utc)
        for esc in active_escalations:
            esc.status = "RESOLVED"
            esc.resolved_at = now
            esc.resolved_reason = resolved_reason
            count += 1
        return count

    @classmethod
    def run_deadline_and_escalation_scan(cls, db: Session, trigger_mode: str = "MANUAL") -> Dict[str, Any]:
        """Comprehensive, cycle-aware deadline evaluation across all 5 regulatory vectors."""
        start_time = time.time()
        now = datetime.now(timezone.utc)
        run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"

        scanned_entities = 0
        reminders_created = 0
        escalations_created = 0
        duplicates_prevented = 0
        resolved_count = 0

        # Load Rule Studio configs
        cure_cfg, cure_ver = get_rule_config(db, "RULE_DEFICIENCY_CURE", {"cure_window_days": 15, "grace_period_days": 3})
        scrutiny_cfg, scrutiny_ver = get_rule_config(db, "RULE_SCRUTINY_SLA", {"sla_days": 7})
        evc_cfg, evc_ver = get_rule_config(db, "RULE_EVC_SCHEDULE", {"max_scheduling_days": 10})
        lease_cfg, lease_ver = get_rule_config(db, "RULE_LEASE_EXPIRY_ALERT", {"warning_threshold_days": [60, 30, 15, 7]})
        comp_cfg, comp_ver = get_rule_config(db, "RULE_COMPLIANCE_UNDERTAKING", {"warning_threshold_days": [15, 7, 0]})

        # =========================================================================
        # VECTOR 1: Compliance Undertakings & Verification
        # =========================================================================
        undertakings = db.query(ComplianceUndertaking).all()
        for u in undertakings:
            scanned_entities += 1
            inst = db.query(Institution).filter(Institution.id == u.institution_id).first()
            region = inst.region if inst else None

            # Auto-resolve if already verified
            if u.status == "VERIFIED":
                resolved_count += cls.auto_resolve_obsolete_escalations(
                    db, "UNDERTAKING", u.id, "Compliance obligation verified by authorized officer"
                )
                continue

            cond = cls.calculate_deadline_condition(u.due_date, reference_time=now)
            days_remaining = cond["days_remaining"]
            cycle_id = f"v{len(u.evidences) + 1}"

            # Approaching deadline reminders: T-15, T-7, T-0
            if days_remaining in [15, 7, 0] or (0 <= days_remaining <= 15 and u.status in ["NOT_YET_DUE", "DUE_SOON"]):
                if u.status == "NOT_YET_DUE" and days_remaining <= 15:
                    u.status = "DUE_SOON"

                threshold = 15 if days_remaining > 7 else (7 if days_remaining > 0 else 0)
                level = "REMINDER_L1" if threshold > 0 else "REMINDER_L2"
                key = generate_idempotency_key("UNDERTAKING", u.id, "DUE_SOON", threshold, level, "COMPLIANCE_OFFICER", cycle_id)
                
                exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                if not exists:
                    esc = AlertEscalation(
                        idempotency_key=key,
                        entity_type="UNDERTAKING",
                        entity_id=u.id,
                        trigger_type="DUE_SOON",
                        threshold_days=threshold,
                        escalation_level=level,
                        recipient_role="COMPLIANCE_OFFICER",
                        institution_id=u.institution_id,
                        region=region,
                        cycle_id=cycle_id,
                        rule_code="RULE_COMPLIANCE_UNDERTAKING",
                        rule_version=comp_ver,
                        status="ACTIVE"
                    )
                    db.add(esc)
                    cls.dispatch_notification(
                        db=db,
                        institution_id=u.institution_id,
                        user_id=u.responsible_user_id,
                        recipient_role="COMPLIANCE_OFFICER",
                        entity_type="UNDERTAKING",
                        entity_id=u.id,
                        title=f"Compliance Due Soon: {u.title}",
                        message=f"Statutory undertaking '{u.title}' is due in {max(0, days_remaining)} days ({u.due_date.strftime('%d %b %Y')}). Please upload required evidence.",
                        level="WARNING" if threshold > 0 else "DANGER",
                        link_url="/compliance"
                    )
                    reminders_created += 1
                else:
                    duplicates_prevented += 1

            # Overdue multi-tier escalations: T+1 (RO), T+7 (BO), T+14 (Member Sec)
            elif days_remaining < 0 and u.status not in ["VERIFIED", "PENDING_VERIFICATION"]:
                u.status = "OVERDUE"
                days_overdue = abs(days_remaining)

                escalation_chain = [
                    (1, "ESCALATION_L1_RO", "REGIONAL_OFFICER"),
                    (7, "ESCALATION_L2_BO", "BUREAU_OFFICER"),
                    (14, "ESCALATION_L3_MEMBER_SEC", "COMPETENT_AUTHORITY")
                ]

                for min_overdue, esc_level, target_role in escalation_chain:
                    if days_overdue >= min_overdue:
                        key = generate_idempotency_key("UNDERTAKING", u.id, "SLA_OVERDUE", min_overdue, esc_level, target_role, cycle_id)
                        exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                        if not exists:
                            esc = AlertEscalation(
                                idempotency_key=key,
                                entity_type="UNDERTAKING",
                                entity_id=u.id,
                                trigger_type="SLA_OVERDUE",
                                threshold_days=min_overdue,
                                escalation_level=esc_level,
                                recipient_role=target_role,
                                institution_id=u.institution_id,
                                region=region,
                                cycle_id=cycle_id,
                                rule_code="RULE_COMPLIANCE_UNDERTAKING",
                                rule_version=comp_ver,
                                status="ACTIVE"
                            )
                            db.add(esc)
                            cls.dispatch_notification(
                                db=db,
                                institution_id=u.institution_id if target_role in ["INSTITUTION_ADMIN", "COMPLIANCE_OFFICER"] else None,
                                user_id=None,
                                recipient_role=target_role,
                                entity_type="UNDERTAKING",
                                entity_id=u.id,
                                title=f"OVERDUE Compliance Alert ({esc_level}): {u.title}",
                                message=f"Undertaking '{u.title}' is overdue by {days_overdue} days. Escalated to {target_role.replace('_', ' ')}.",
                                level="DANGER",
                                link_url="/compliance"
                            )
                            escalations_created += 1
                        else:
                            duplicates_prevented += 1

        # =========================================================================
        # VECTOR 2: Document Validity & Renewals
        # =========================================================================
        documents = db.query(DocumentRecord).all()
        for doc in documents:
            if not doc.expiry_date:
                continue
            scanned_entities += 1
            inst = db.query(Institution).filter(Institution.id == doc.institution_id).first()
            region = inst.region if inst else None

            cond = cls.calculate_deadline_condition(doc.expiry_date, reference_time=now)
            days_to_expiry = cond["days_remaining"]
            cycle_id = f"v{doc.current_version}"

            # Auto-resolve old expiry escalations if renewed and verified
            if doc.status == "ACTIVE" and days_to_expiry > 60:
                resolved_count += cls.auto_resolve_obsolete_escalations(
                    db, "DOCUMENT", doc.id, "Document renewed and verified with extended validity"
                )
                continue

            # Expiring soon reminders: T-60, T-30, T-15, T-7
            for thresh in [60, 30, 15, 7]:
                if days_to_expiry <= thresh and days_to_expiry >= 0:
                    if doc.status == "ACTIVE":
                        doc.status = "EXPIRING_SOON"

                    key = generate_idempotency_key("DOCUMENT", doc.id, "EXPIRY_WARNING", thresh, "REMINDER_L1", "INSTITUTION_ADMIN", cycle_id)
                    exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                    if not exists:
                        esc = AlertEscalation(
                            idempotency_key=key,
                            entity_type="DOCUMENT",
                            entity_id=doc.id,
                            trigger_type="EXPIRY_WARNING",
                            threshold_days=thresh,
                            escalation_level="REMINDER_L1",
                            recipient_role="INSTITUTION_ADMIN",
                            institution_id=doc.institution_id,
                            region=region,
                            cycle_id=cycle_id,
                            rule_code="RULE_LEASE_EXPIRY_ALERT",
                            rule_version=lease_ver,
                            status="ACTIVE"
                        )
                        db.add(esc)
                        cls.dispatch_notification(
                            db=db,
                            institution_id=doc.institution_id,
                            user_id=None,
                            recipient_role="INSTITUTION_ADMIN",
                            entity_type="DOCUMENT",
                            entity_id=doc.id,
                            title=f"Document Expiring Soon ({thresh}d window): {doc.title}",
                            message=f"Prescribed document '{doc.title}' expires in {days_to_expiry} days on {doc.expiry_date.strftime('%d %b %Y')}. Please submit renewal.",
                            level="WARNING",
                            link_url="/documents"
                        )
                        reminders_created += 1
                    else:
                        duplicates_prevented += 1

            # Expired document escalations: T+1 (RO), T+15 (BO)
            if days_to_expiry < 0 and doc.status != "RENEWAL_SUBMITTED":
                if doc.status != "EXPIRED":
                    doc.status = "EXPIRED"

                days_expired = abs(days_to_expiry)
                for min_exp, esc_lvl, target_role in [(1, "ESCALATION_L1_RO", "REGIONAL_OFFICER"), (15, "ESCALATION_L2_BO", "BUREAU_OFFICER")]:
                    if days_expired >= min_exp:
                        key = generate_idempotency_key("DOCUMENT", doc.id, "EXPIRED", min_exp, esc_lvl, target_role, cycle_id)
                        exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                        if not exists:
                            esc = AlertEscalation(
                                idempotency_key=key,
                                entity_type="DOCUMENT",
                                entity_id=doc.id,
                                trigger_type="EXPIRED",
                                threshold_days=min_exp,
                                escalation_level=esc_lvl,
                                recipient_role=target_role,
                                institution_id=doc.institution_id,
                                region=region,
                                cycle_id=cycle_id,
                                rule_code="RULE_LEASE_EXPIRY_ALERT",
                                rule_version=lease_ver,
                                status="ACTIVE"
                            )
                            db.add(esc)
                            cls.dispatch_notification(
                                db=db,
                                institution_id=doc.institution_id if target_role == "INSTITUTION_ADMIN" else None,
                                user_id=None,
                                recipient_role=target_role,
                                entity_type="DOCUMENT",
                                entity_id=doc.id,
                                title=f"EXPIRED Document Escalation: {doc.title}",
                                message=f"Document '{doc.title}' expired {days_expired} days ago on {doc.expiry_date.strftime('%d %b %Y')}. Escalated to {target_role}.",
                                level="DANGER",
                                link_url="/documents"
                            )
                            escalations_created += 1
                        else:
                            duplicates_prevented += 1

        # =========================================================================
        # VECTOR 3: Application Stage SLAs & Deficiency Cure Window
        # =========================================================================
        applications = db.query(Application).all()
        for app in applications:
            scanned_entities += 1
            inst = db.query(Institution).filter(Institution.id == app.institution_id).first()
            region = inst.region if inst else None

            # If no longer in DEFICIENCY_COMMUNICATED, auto-resolve cure window escalations
            if app.current_stage != "DEFICIENCY_COMMUNICATED":
                resolved_count += cls.auto_resolve_obsolete_escalations(
                    db, "APPLICATION", app.id, f"Application transitioned to stage {app.current_stage}"
                )

            updated = app.updated_at or app.created_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_in_stage = (now - updated).days
            cycle_id = f"v{app.version}"

            # 3A: Deficiency Cure Window (Default 15 days)
            if app.current_stage == "DEFICIENCY_COMMUNICATED":
                cure_days = cure_cfg.get("cure_window_days", 15)
                days_left = cure_days - days_in_stage

                # Approaching cure deadline reminder (at 5 days and 2 days left)
                for thresh_left in [5, 2]:
                    if days_left <= thresh_left and days_left >= 0:
                        key = generate_idempotency_key("APPLICATION", app.id, "DEFICIENCY_CURE_WARNING", thresh_left, "REMINDER_L1", "INSTITUTION_ADMIN", cycle_id)
                        exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                        if not exists:
                            esc = AlertEscalation(
                                idempotency_key=key,
                                entity_type="APPLICATION",
                                entity_id=app.id,
                                trigger_type="DEFICIENCY_CURE_WARNING",
                                threshold_days=thresh_left,
                                escalation_level="REMINDER_L1",
                                recipient_role="INSTITUTION_ADMIN",
                                institution_id=app.institution_id,
                                region=region,
                                cycle_id=cycle_id,
                                rule_code="RULE_DEFICIENCY_CURE",
                                rule_version=cure_ver,
                                status="ACTIVE"
                            )
                            db.add(esc)
                            cls.dispatch_notification(
                                db=db,
                                institution_id=app.institution_id,
                                user_id=None,
                                recipient_role="INSTITUTION_ADMIN",
                                entity_type="APPLICATION",
                                entity_id=app.id,
                                title=f"Urgent: Deficiency Cure Window Closing for {app.application_number}",
                                message=f"Application {app.application_number} has {days_left} days remaining to cure deficiencies before statutory escalation.",
                                level="WARNING",
                                link_url=f"/applications/{app.id}"
                            )
                            reminders_created += 1
                        else:
                            duplicates_prevented += 1

                # Overdue deficiency escalations: T+1 (RO), T+5 (BO), T+10 (Member Sec)
                if days_in_stage > cure_days:
                    breach_days = days_in_stage - cure_days
                    for min_breach, esc_lvl, target_role in [(1, "ESCALATION_L1_RO", "REGIONAL_OFFICER"), (5, "ESCALATION_L2_BO", "BUREAU_OFFICER"), (10, "ESCALATION_L3_MEMBER_SEC", "COMPETENT_AUTHORITY")]:
                        if breach_days >= min_breach:
                            key = generate_idempotency_key("APPLICATION", app.id, "DEFICIENCY_OVERDUE", min_breach, esc_lvl, target_role, cycle_id)
                            exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                            if not exists:
                                esc = AlertEscalation(
                                    idempotency_key=key,
                                    entity_type="APPLICATION",
                                    entity_id=app.id,
                                    trigger_type="DEFICIENCY_OVERDUE",
                                    threshold_days=min_breach,
                                    escalation_level=esc_lvl,
                                    recipient_role=target_role,
                                    institution_id=app.institution_id,
                                    region=region,
                                    cycle_id=cycle_id,
                                    rule_code="RULE_DEFICIENCY_CURE",
                                    rule_version=cure_ver,
                                    status="ACTIVE"
                                )
                                db.add(esc)
                                cls.dispatch_notification(
                                    db=db,
                                    institution_id=app.institution_id if target_role == "INSTITUTION_ADMIN" else None,
                                    user_id=None,
                                    recipient_role=target_role,
                                    entity_type="APPLICATION",
                                    entity_id=app.id,
                                    title=f"CRITICAL ESCALATION: Deficiency Window Breached ({esc_lvl}) for {app.application_number}",
                                    message=f"Application {app.application_number} exceeded 15-day cure SLA by {breach_days} days. Escalated to {target_role}.",
                                    level="DANGER",
                                    link_url=f"/applications/{app.id}"
                                )
                                escalations_created += 1
                            else:
                                duplicates_prevented += 1

            # 3B: Scrutiny Pendency SLA (Default 7 days in SUBMITTED)
            elif app.current_stage == "SUBMITTED":
                sla_days = scrutiny_cfg.get("sla_days", 7)
                if days_in_stage >= sla_days:
                    breach = days_in_stage - sla_days
                    key = generate_idempotency_key("APPLICATION", app.id, "SCRUTINY_SLA_BREACH", sla_days, "ESCALATION_L1_RO", "REGIONAL_OFFICER", cycle_id)
                    exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                    if not exists:
                        esc = AlertEscalation(
                            idempotency_key=key,
                            entity_type="APPLICATION",
                            entity_id=app.id,
                            trigger_type="SCRUTINY_SLA_BREACH",
                            threshold_days=sla_days,
                            escalation_level="ESCALATION_L1_RO",
                            recipient_role="REGIONAL_OFFICER",
                            institution_id=app.institution_id,
                            region=region,
                            cycle_id=cycle_id,
                            rule_code="RULE_SCRUTINY_SLA",
                            rule_version=scrutiny_ver,
                            status="ACTIVE"
                        )
                        db.add(esc)
                        cls.dispatch_notification(
                            db=db,
                            institution_id=None,
                            user_id=app.scrutiny_officer_id,
                            recipient_role="REGIONAL_OFFICER",
                            entity_type="APPLICATION",
                            entity_id=app.id,
                            title=f"Scrutiny SLA Breached: {app.application_number}",
                            message=f"Application {app.application_number} has been awaiting scrutiny for {days_in_stage} days (SLA: {sla_days} days).",
                            level="WARNING",
                            link_url=f"/officer/applications/{app.id}"
                        )
                        escalations_created += 1
                    else:
                        duplicates_prevented += 1

            # 3C: EVC Scheduling SLA (Default 10 days in AWAITING_EVC_SCHEDULE)
            elif app.current_stage == "AWAITING_EVC_SCHEDULE":
                sched_sla = evc_cfg.get("max_scheduling_days", 10)
                if days_in_stage >= sched_sla:
                    key = generate_idempotency_key("APPLICATION", app.id, "EVC_SCHEDULE_OVERDUE", sched_sla, "ESCALATION_L1_RO", "EVC_COORDINATOR", cycle_id)
                    exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                    if not exists:
                        esc = AlertEscalation(
                            idempotency_key=key,
                            entity_type="APPLICATION",
                            entity_id=app.id,
                            trigger_type="EVC_SCHEDULE_OVERDUE",
                            threshold_days=sched_sla,
                            escalation_level="ESCALATION_L1_RO",
                            recipient_role="EVC_COORDINATOR",
                            institution_id=app.institution_id,
                            region=region,
                            cycle_id=cycle_id,
                            rule_code="RULE_EVC_SCHEDULE",
                            rule_version=evc_ver,
                            status="ACTIVE"
                        )
                        db.add(esc)
                        cls.dispatch_notification(
                            db=db,
                            institution_id=None,
                            user_id=None,
                            recipient_role="EVC_COORDINATOR",
                            entity_type="APPLICATION",
                            entity_id=app.id,
                            title=f"EVC Scheduling Overdue: {app.application_number}",
                            message=f"Application {app.application_number} has been awaiting EVC inspection scheduling for {days_in_stage} days (SLA: {sched_sla} days).",
                            level="WARNING",
                            link_url="/officer/evc"
                        )
                        escalations_created += 1
                    else:
                        duplicates_prevented += 1

        # =========================================================================
        # VECTOR 4: EVC Inspection Report Pendency
        # =========================================================================
        evc_inspections = db.query(EVCInspection).filter(
            EVCInspection.status.in_(["SCHEDULED", "IN_PROGRESS"])
        ).all()
        for evc in evc_inspections:
            scanned_entities += 1
            if evc.scheduled_date:
                sched_dt = evc.scheduled_date
                if sched_dt.tzinfo is None:
                    sched_dt = sched_dt.replace(tzinfo=timezone.utc)
                if now > sched_dt:
                    days_post_visit = (now - sched_dt).days
                    if days_post_visit >= 3:
                        key = generate_idempotency_key("EVC", evc.id, "EVC_REPORT_PENDING", 3, "ESCALATION_L1_RO", "EVC_COORDINATOR", "1")
                        exists = db.query(AlertEscalation).filter(AlertEscalation.idempotency_key == key).first()
                        if not exists:
                            esc = AlertEscalation(
                                idempotency_key=key,
                                entity_type="EVC",
                                entity_id=evc.id,
                                trigger_type="EVC_REPORT_PENDING",
                                threshold_days=3,
                                escalation_level="ESCALATION_L1_RO",
                                recipient_role="EVC_COORDINATOR",
                                region=evc.region,
                                status="ACTIVE"
                            )
                            db.add(esc)
                            cls.dispatch_notification(
                                db=db,
                                institution_id=evc.institution_id,
                                user_id=evc.coordinator_id,
                                recipient_role="EVC_COORDINATOR",
                                entity_type="EVC",
                                entity_id=evc.id,
                                title=f"EVC Inspection Report Overdue",
                                message=f"EVC visit conducted on {sched_dt.strftime('%d %b %Y')} has not submitted its final report ({days_post_visit} days elapsed).",
                                level="WARNING",
                                link_url="/officer/evc"
                            )
                            escalations_created += 1
                        else:
                            duplicates_prevented += 1

        db.commit()
        exec_time = (time.time() - start_time) * 1000.0

        # Record run history
        run_record = DeadlineEngineRun(
            run_id=run_id,
            trigger_mode=trigger_mode,
            scanned_entities=scanned_entities,
            reminders_created=reminders_created,
            escalations_created=escalations_created,
            duplicates_prevented=duplicates_prevented,
            resolved_count=resolved_count,
            execution_time_ms=round(exec_time, 2),
            status="SUCCESS",
            created_at=datetime.now(timezone.utc)
        )
        db.add(run_record)
        db.commit()

        return {
            "run_id": run_id,
            "trigger_mode": trigger_mode,
            "scanned_entities": scanned_entities,
            "reminders_created": reminders_created,
            "escalations_created": escalations_created,
            "duplicates_prevented": duplicates_prevented,
            "resolved_count": resolved_count,
            "execution_time_ms": round(exec_time, 2)
        }

# Backwards compatibility helper
run_deadline_and_escalation_scan = DeadlineService.run_deadline_and_escalation_scan

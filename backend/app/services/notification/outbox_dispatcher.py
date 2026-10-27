import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.config import settings
from app.models.notification_outbox import NotificationOutbox
from app.models.alert import Notification
from app.services.notification.providers import get_email_provider, get_sms_provider, ProviderResult
from app.services.notification.templates import NotificationTemplateEngine
from app.services.notification.sse_broker import get_sse_broker
from app.services.notification.auth_policy import (
    build_canonical_recipient_id,
    redact_sensitive_text
)
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)


class OutboxDispatcherService:
    """
    Transactional Notification Outbox Dispatcher with Atomic Claims & Concurrency Protection.
    - Guarantees non-blocking, reliable, observable notification delivery with bounded backoff retries.
    - Atomically records dispatches inside originating business transactions.
    - Implements durable row claims (SKIP LOCKED in PostgreSQL / atomic conditional claims in SQLite).
    - Releases database transactions during external network calls to avoid blocking connection pools.
    - Automatically recovers crashed worker claims via lease timeouts without stranding records.
    """

    DEFAULT_PROCESSING_LEASE_SECONDS = 300

    @classmethod
    def queue_notification(
        cls,
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: int,
        channel: str,  # EMAIL, SMS, IN_APP
        template_code: str,
        params: Dict[str, Any],
        institution_id: Optional[int] = None,
        region: Optional[str] = None,
        recipient_role: Optional[str] = None,
        recipient_user_id: Optional[int] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        link_url: Optional[str] = None,
        level: str = "INFO"
    ) -> NotificationOutbox:
        """
        Enqueues an outbox dispatch record within the caller's active database transaction.
        Guarantees zero lost events between database mutations and notification delivery.
        """
        corr_id = correlation_id or str(uuid.uuid4())
        eff_link = link_url or params.get("link_url")

        # Derive subject and bodies via template engine
        params["link_url"] = eff_link
        subject, body_text, body_html = NotificationTemplateEngine.render(template_code, params)

        # Generate deterministic idempotency key if not provided
        if not idempotency_key:
            canon_recip = build_canonical_recipient_id(
                recipient_user_id=recipient_user_id,
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                recipient_role=recipient_role
            )
            cycle_val = params.get("cycle_id") or params.get("delivery_cycle")
            cycle_part = f":CYCLE:{cycle_val}" if cycle_val else ""
            idempotency_key = f"OUTBOX:{entity_type}:{entity_id}:{channel}:{event_type}{cycle_part}:{canon_recip}"

        # Check existing outbox record to prevent duplicate enqueuing
        existing = db.query(NotificationOutbox).filter(
            NotificationOutbox.idempotency_key == idempotency_key
        ).first()

        if existing:
            return existing

        outbox_item = NotificationOutbox(
            idempotency_key=idempotency_key,
            correlation_id=corr_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            institution_id=institution_id,
            region=region,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            channel=channel,
            template_code=template_code,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            link_url=eff_link,
            payload_json=params,
            status="QUEUED",
            attempt_count=0,
            max_attempts=getattr(settings, "NOTIFICATION_OUTBOX_MAX_RETRIES", 4),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(outbox_item)
        db.flush()  # Flush to acquire outbox_item.id within current transaction

        # For IN_APP channel or hybrid dispatches, record immediate Notification inbox item
        if channel == "IN_APP":
            notif = Notification(
                user_id=recipient_user_id,
                institution_id=institution_id,
                recipient_role=recipient_role,
                entity_type=entity_type,
                entity_id=entity_id,
                title=subject,
                message=body_text,
                channel="IN_APP",
                delivery_channel="IN_APP",
                delivery_status="DELIVERED",
                level=level,
                is_read=False,
                link_url=eff_link,
                outbox_id=outbox_item.id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(notif)
            outbox_item.status = "ACCEPTED_BY_PROVIDER"
            outbox_item.sent_at = datetime.now(timezone.utc)
            outbox_item.provider_message_id = f"INAPP-{outbox_item.id}"
            outbox_item.provider_response = "Internal inbox notification persisted successfully"

        return outbox_item

    @classmethod
    def claim_outbox_batch(
        cls,
        db: Session,
        batch_size: int = 50,
        lease_seconds: Optional[int] = None
    ) -> List[int]:
        """
        Atomically claims a batch of claimable outbox records.
        - Only one active worker can claim a specific record.
        - Claim is durably committed to the database before network dispatch begins.
        - Stale PROCESSING claims from crashed workers recover safely after lease timeout.
        - Uses SKIP LOCKED on PostgreSQL, atomic conditional claims on SQLite.
        """
        lease = lease_seconds or cls.DEFAULT_PROCESSING_LEASE_SECONDS
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(seconds=lease)

        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind else ""
        claimed_ids: List[int] = []

        if dialect_name == "postgresql":
            candidates = (
                db.query(NotificationOutbox)
                .filter(
                    or_(
                        NotificationOutbox.status == "QUEUED",
                        and_(
                            NotificationOutbox.status == "RETRY_SCHEDULED",
                            or_(NotificationOutbox.next_retry_at == None, NotificationOutbox.next_retry_at <= now)
                        ),
                        and_(
                            NotificationOutbox.status == "PROCESSING",
                            NotificationOutbox.last_attempt_at <= stale_threshold
                        )
                    )
                )
                .order_by(NotificationOutbox.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(batch_size)
                .all()
            )
            for item in candidates:
                item.status = "PROCESSING"
                item.last_attempt_at = now
                item.attempt_count += 1
                item.updated_at = now
                claimed_ids.append(item.id)
            db.commit()
        else:
            # SQLite / Generic Dialect Atomic Conditional Claim
            candidate_ids = [
                r[0] for r in (
                    db.query(NotificationOutbox.id)
                    .filter(
                        or_(
                            NotificationOutbox.status == "QUEUED",
                            and_(
                                NotificationOutbox.status == "RETRY_SCHEDULED",
                                or_(NotificationOutbox.next_retry_at == None, NotificationOutbox.next_retry_at <= now)
                            ),
                            and_(
                                NotificationOutbox.status == "PROCESSING",
                                NotificationOutbox.last_attempt_at <= stale_threshold
                            )
                        )
                    )
                    .order_by(NotificationOutbox.created_at.asc())
                    .limit(batch_size)
                    .all()
                )
            ]

            for cid in candidate_ids:
                rowcount = (
                    db.query(NotificationOutbox)
                    .filter(
                        NotificationOutbox.id == cid,
                        or_(
                            NotificationOutbox.status == "QUEUED",
                            and_(
                                NotificationOutbox.status == "RETRY_SCHEDULED",
                                or_(NotificationOutbox.next_retry_at == None, NotificationOutbox.next_retry_at <= now)
                            ),
                            and_(
                                NotificationOutbox.status == "PROCESSING",
                                NotificationOutbox.last_attempt_at <= stale_threshold
                            )
                        )
                    )
                    .update({
                        NotificationOutbox.status: "PROCESSING",
                        NotificationOutbox.last_attempt_at: now,
                        NotificationOutbox.attempt_count: NotificationOutbox.attempt_count + 1,
                        NotificationOutbox.updated_at: now
                    }, synchronize_session=False)
                )
                if rowcount == 1:
                    db.commit()
                    claimed_ids.append(cid)
                else:
                    db.rollback()

        return claimed_ids

    @classmethod
    def dispatch_pending_outbox(
        cls,
        db: Session,
        batch_size: int = 50,
        lease_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Background outbox processing worker.
        1. Atomically claims records with durable status=PROCESSING.
        2. Transmits via providers without holding DB transaction open.
        3. Records outcome with bounded exponential backoff and DEAD_LETTER transitions.
        """
        claimed_ids = cls.claim_outbox_batch(db, batch_size=batch_size, lease_seconds=lease_seconds)

        summary = {
            "scanned": len(claimed_ids),
            "accepted": 0,
            "simulated": 0,
            "not_configured": 0,
            "retry_scheduled": 0,
            "dead_letter": 0,
            "failed": 0
        }

        sse_broker = get_sse_broker()

        for item_id in claimed_ids:
            item = db.query(NotificationOutbox).filter(NotificationOutbox.id == item_id).first()
            if not item:
                continue

            cls._execute_network_dispatch(db, item, sse_broker=sse_broker)

            if item.status == "ACCEPTED_BY_PROVIDER":
                summary["accepted"] += 1
            elif item.status == "SIMULATED":
                summary["simulated"] += 1
            elif item.status == "NOT_CONFIGURED":
                summary["not_configured"] += 1
            elif item.status == "RETRY_SCHEDULED":
                summary["retry_scheduled"] += 1
            elif item.status == "DEAD_LETTER":
                summary["dead_letter"] += 1
            elif item.status == "FAILED":
                summary["failed"] += 1

        return summary

    @classmethod
    def dispatch_single_item(
        cls,
        db: Session,
        outbox_id: int
    ) -> Optional[NotificationOutbox]:
        """
        Dispatches ONLY the specific targeted outbox item without triggering unrelated batch items.
        Used for safe manual retries.
        """
        item = db.query(NotificationOutbox).filter(NotificationOutbox.id == outbox_id).first()
        if not item:
            return None

        now = datetime.now(timezone.utc)
        item.status = "PROCESSING"
        item.last_attempt_at = now
        item.attempt_count += 1
        item.updated_at = now
        db.commit()
        db.refresh(item)

        cls._execute_network_dispatch(db, item, sse_broker=get_sse_broker())
        return item

    @classmethod
    def dispatch_outbox_item(
        cls,
        db: Session,
        item: NotificationOutbox,
        sse_broker=None
    ) -> NotificationOutbox:
        """
        Executes delivery dispatch for a single NotificationOutbox record.
        Maintains backward compatibility for tests calling dispatch_outbox_item directly.
        """
        now = datetime.now(timezone.utc)
        item.status = "PROCESSING"
        item.last_attempt_at = now
        item.attempt_count += 1
        item.updated_at = now
        db.commit()
        db.refresh(item)

        cls._execute_network_dispatch(db, item, sse_broker=sse_broker or get_sse_broker())
        return item

    @classmethod
    def _execute_network_dispatch(
        cls,
        db: Session,
        item: NotificationOutbox,
        sse_broker=None
    ) -> None:
        """
        Executes external network dispatch outside long DB locks.
        Applies standardized error classification, bounded exponential backoff, and state persistence.
        """
        email_prov = get_email_provider()
        sms_prov = get_sms_provider()
        broker = sse_broker or get_sse_broker()

        result: ProviderResult
        if item.channel == "EMAIL":
            result = email_prov.send(
                recipient_email=item.recipient_email,
                recipient_phone=None,
                subject=item.subject,
                body_text=item.body_text,
                body_html=item.body_html,
                metadata={"correlation_id": item.correlation_id, "entity_id": item.entity_id}
            )
        elif item.channel == "SMS":
            result = sms_prov.send(
                recipient_email=None,
                recipient_phone=item.recipient_phone,
                subject=item.subject,
                body_text=item.body_text,
                body_html=None,
                metadata={"correlation_id": item.correlation_id, "entity_id": item.entity_id}
            )
        elif item.channel == "IN_APP":
            result = ProviderResult(
                status="ACCEPTED_BY_PROVIDER",
                provider_message_id=f"INAPP-{item.id}",
                response_message="In-app notification ready."
            )
        else:
            result = ProviderResult(
                status="FAILED",
                error_category="UNSUPPORTED_CHANNEL",
                error_message=f"Unsupported communication channel '{item.channel}'"
            )

        # Apply outcome state machine
        now = datetime.now(timezone.utc)
        item.last_error_category = result.error_category
        item.last_error_message = redact_sensitive_text(result.error_message)
        item.provider_message_id = result.provider_message_id
        item.provider_response = redact_sensitive_text(result.response_message)
        item.updated_at = now

        if result.status == "ACCEPTED_BY_PROVIDER":
            item.status = "ACCEPTED_BY_PROVIDER"
            item.sent_at = now
        elif result.status == "SIMULATED":
            item.status = "SIMULATED"
            item.sent_at = now
        elif result.status == "NOT_CONFIGURED":
            item.status = "NOT_CONFIGURED"
        elif result.status in ["RETRY_SCHEDULED", "FAILED"]:
            if item.attempt_count < item.max_attempts:
                base_sec = getattr(settings, "NOTIFICATION_OUTBOX_RETRY_BACKOFF_BASE_SECONDS", 60)
                backoff_secs = base_sec * (2 ** (item.attempt_count - 1))
                item.next_retry_at = now + timedelta(seconds=backoff_secs)
                item.status = "RETRY_SCHEDULED"
            else:
                item.status = "DEAD_LETTER"
                item.last_error_category = result.error_category or "MAX_ATTEMPTS_EXCEEDED"
                item.last_error_message = f"Terminal delivery failure: exceeded max {item.max_attempts} attempts. Last: {result.error_message}"

        # Broadcast to SSE broker asynchronously if active event loop
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(broker.broadcast_event(
                    event_type=item.event_type,
                    data={
                        "title": item.subject,
                        "body_text": item.body_text,
                        "level": "INFO",
                        "entity_type": item.entity_type,
                        "entity_id": item.entity_id,
                        "link_url": item.link_url,
                        "institution_id": item.institution_id,
                        "recipient_role": item.recipient_role,
                        "recipient_user_id": item.recipient_user_id,
                        "region": item.region
                    }
                ))
        except RuntimeError:
            pass
        except Exception:
            pass

        db.commit()
        db.refresh(item)

    @classmethod
    def manual_retry(
        cls,
        db: Session,
        outbox_id: int,
        current_user,
        active_role: Optional[str] = None
    ) -> NotificationOutbox:
        """
        Allows authorized administrators to reset and re-dispatch failed or dead-letter outbox records.
        Records an immutable audit event with the actual acting role.
        """
        item = db.query(NotificationOutbox).filter(NotificationOutbox.id == outbox_id).first()
        if not item:
            raise ValueError(f"NotificationOutbox #{outbox_id} not found")

        prev_status = item.status
        item.status = "QUEUED"
        item.attempt_count = 0
        item.next_retry_at = None
        item.last_error_message = f"Manual retry initiated by {getattr(current_user, 'full_name', 'Admin')} (Previous status: {prev_status})"
        item.updated_at = datetime.now(timezone.utc)

        # Derive actual actor role accurately
        user_roles = [r.role for r in getattr(current_user, "roles", [])]
        if active_role and active_role in user_roles:
            actor_role = active_role
        elif "REGIONAL_OFFICER" in user_roles and item.region and getattr(current_user, "region", None) == item.region:
            actor_role = "REGIONAL_OFFICER"
        elif "BUREAU_OFFICER" in user_roles:
            actor_role = "BUREAU_OFFICER"
        elif "SYSTEM_ADMIN" in user_roles:
            actor_role = "SYSTEM_ADMIN"
        elif user_roles:
            actor_role = user_roles[0]
        else:
            actor_role = "SYSTEM_ADMIN"

        log_audit_event(
            db=db,
            action="NOTIFICATION_OUTBOX_MANUAL_RETRY",
            entity_type="NOTIFICATION_OUTBOX",
            entity_id=item.id,
            actor_id=getattr(current_user, "id", None),
            actor_name=getattr(current_user, "full_name", None),
            actor_role=actor_role,
            institution_id=item.institution_id,
            details={
                "outbox_id": item.id,
                "event_type": item.event_type,
                "channel": item.channel,
                "previous_status": prev_status,
                "actual_actor_role": actor_role
            }
        )

        db.commit()
        db.refresh(item)
        return item

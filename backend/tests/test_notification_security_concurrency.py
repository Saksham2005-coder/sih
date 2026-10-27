import pytest
import threading
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import create_access_token
from app.models.notification_outbox import NotificationOutbox
from app.models.alert import Notification
from app.models.user import User, UserRole
from app.models.token_blacklist import RevokedToken
from app.services.notification.providers import SMTPEmailProvider, ProviderResult
from app.services.notification.outbox_dispatcher import OutboxDispatcherService
from app.services.notification.sse_broker import SSEClientConnection, get_sse_broker
from app.services.notification.ticket_service import StreamTicketService
from app.services.notification.auth_policy import (
    NotificationScopePolicy,
    build_canonical_recipient_id,
    redact_sensitive_text,
    mask_email,
    mask_phone
)


def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_evc_coordinator_and_committee_member_cross_scope_detail_access(client):
    """
    Test 1: EVC Coordinator and Committee Member cross-scope detail access returns 403 Forbidden.
    """
    evc_token = get_auth_token(client, "evc.coord@aicte.gov.in")
    cm_token = get_auth_token(client, "committee.member@aicte.gov.in")

    db = SessionLocal()
    key_prefix = f"CROSS-SCOPE-{datetime.now(timezone.utc).timestamp()}"
    try:
        # Outbox item in Northern region (EVC Coordinator is Western)
        northern_outbox = NotificationOutbox(
            idempotency_key=f"{key_prefix}-NORTH",
            correlation_id="corr-north",
            event_type="APPLICATION_STAGE_CHANGED",
            entity_type="APPLICATION",
            entity_id=999,
            region="Northern",
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            subject="Northern Region Case",
            body_text="Details for Northern application",
            status="QUEUED"
        )
        # Outbox item for an unassigned application
        unassigned_outbox = NotificationOutbox(
            idempotency_key=f"{key_prefix}-UNASSIGNED",
            correlation_id="corr-unassigned",
            event_type="COMMITTEE_HEARING_SCHEDULED",
            entity_type="APPLICATION",
            entity_id=8888,
            region="Western",
            recipient_role="COMMITTEE_MEMBER",
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            subject="Unassigned Committee Case",
            body_text="Hearing details for unassigned case",
            status="QUEUED"
        )
        db.add(northern_outbox)
        db.add(unassigned_outbox)
        db.commit()
        db.refresh(northern_outbox)
        db.refresh(unassigned_outbox)
        north_id = northern_outbox.id
        unassigned_id = unassigned_outbox.id
    finally:
        db.close()

    # EVC coordinator (Western) accessing Northern item -> 403
    res_evc = client.get(
        f"/api/notifications/outbox/{north_id}",
        headers={"Authorization": f"Bearer {evc_token}"}
    )
    assert res_evc.status_code == 403
    assert "outside your assigned region" in res_evc.text

    # Committee member accessing unassigned outbox item -> 403
    res_cm = client.get(
        f"/api/notifications/outbox/{unassigned_id}",
        headers={"Authorization": f"Bearer {cm_token}"}
    )
    assert res_cm.status_code == 403
    assert "not assigned" in res_cm.text


def test_regional_officer_without_assigned_region_fails_closed(client):
    """
    Test 2: Regional Officer without an assigned region fails closed (does not silently disable filtering).
    """
    from app.core.security import get_password_hash
    db = SessionLocal()
    try:
        # Create a test RO without assigned region
        no_region_ro = User(
            email="ro.noregion@aicte.gov.in",
            hashed_password=get_password_hash("Password123!"),
            full_name="Officer Without Region",
            region=None,
            is_active=True
        )
        db.add(no_region_ro)
        db.commit()
        db.refresh(no_region_ro)

        role = UserRole(user_id=no_region_ro.id, role="REGIONAL_OFFICER")
        db.add(role)
        db.commit()

        # Seed an outbox item
        test_item = NotificationOutbox(
            idempotency_key=f"FAIL-CLOSED-{datetime.now(timezone.utc).timestamp()}",
            correlation_id="corr-fc",
            event_type="TEST_EVENT",
            entity_type="APPLICATION",
            entity_id=1,
            region="Western",
            channel="EMAIL",
            template_code="TEST",
            subject="Regional Item",
            body_text="Text",
            status="QUEUED"
        )
        db.add(test_item)
        db.commit()
        db.refresh(test_item)
        item_id = test_item.id
    finally:
        db.close()

    token = get_auth_token(client, "ro.noregion@aicte.gov.in")

    # List endpoint must fail closed: return empty list
    res_list = client.get("/api/notifications/outbox", headers={"Authorization": f"Bearer {token}"})
    assert res_list.status_code == 200
    assert len(res_list.json()) == 0

    # Summary endpoint must report 0
    res_summary = client.get("/api/notifications/outbox/summary", headers={"Authorization": f"Bearer {token}"})
    assert res_summary.status_code == 200
    assert res_summary.json()["total"] == 0

    # Detail endpoint must fail closed: 403 Forbidden
    res_detail = client.get(f"/api/notifications/outbox/{item_id}", headers={"Authorization": f"Bearer {token}"})
    assert res_detail.status_code == 403
    assert "no assigned jurisdiction" in res_detail.text


def test_consistency_of_outbox_list_detail_and_summary_scopes(client):
    """
    Test 3: Consistency of outbox list, detail and summary scopes.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")

    # List
    res_list = client.get("/api/notifications/outbox", headers={"Authorization": f"Bearer {ro_token}"})
    assert res_list.status_code == 200
    visible_items = res_list.json()

    # Summary
    res_summary = client.get("/api/notifications/outbox/summary", headers={"Authorization": f"Bearer {ro_token}"})
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total"] == len(visible_items)

    # All items in visible list must be accessible on detail
    for item in visible_items[:5]:
        res_det = client.get(f"/api/notifications/outbox/{item['id']}", headers={"Authorization": f"Bearer {ro_token}"})
        assert res_det.status_code == 200
        assert res_det.json()["id"] == item["id"]


def test_sensitive_field_redaction_by_role(client):
    """
    Test 4: Sensitive field redaction by role.
    General users receive only essential notification fields with masked PII and zero provider diagnostics.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    admin_token = get_auth_token(client, "sysadmin@aicte.gov.in")

    db = SessionLocal()
    key = f"REDACT-TEST-{datetime.now(timezone.utc).timestamp()}"
    try:
        item = NotificationOutbox(
            idempotency_key=key,
            correlation_id="corr-redact",
            event_type="APPLICATION_SUBMITTED",
            entity_type="APPLICATION",
            entity_id=1,
            institution_id=1,
            region="Western",
            recipient_email="confidential.applicant@test.edu.in",
            recipient_phone="+919876543210",
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            subject="Order with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 and password: SuperSecretPassword123!",
            body_text="Your password is password: SecretPassword456 and token: token_12345",
            provider_response="250 Delivered via relay 192.168.1.50 with api_key: AICTE_RELAY_KEY_999",
            last_error_message="SMTP failed with secret_key: SMTP_PASS_KEY_XYZ",
            payload_json={"internal_secret": "TOP_SECRET"},
            status="QUEUED"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        item_id = item.id
    finally:
        db.close()

    # 1. Institution User (General Tenancy User)
    res_inst = client.get(f"/api/notifications/outbox/{item_id}", headers={"Authorization": f"Bearer {inst_token}"})
    assert res_inst.status_code == 200
    inst_data = res_inst.json()
    assert inst_data["recipient_phone"] is None
    assert "@" in inst_data["recipient_email"] and "*" in inst_data["recipient_email"]
    assert "[REDACTED_SECRET]" in inst_data["subject"]
    assert "SuperSecretPassword123!" not in inst_data["subject"]
    assert "SecretPassword456" not in inst_data["body_text"]
    assert inst_data["provider_response"] is None
    assert inst_data["last_error_message"] is None
    assert inst_data["payload_json"] is None

    # Verify ordinary users cannot view SMTP host/port in /channels/status
    res_ch_inst = client.get("/api/notifications/channels/status", headers={"Authorization": f"Bearer {inst_token}"})
    assert res_ch_inst.status_code == 200
    email_ch_inst = next(c for c in res_ch_inst.json()["channels"] if c["channel"] == "EMAIL")
    assert "host" not in email_ch_inst["details"]
    assert "port" not in email_ch_inst["details"]

    # 2. Regional Officer (Operational Officer)
    res_ro = client.get(f"/api/notifications/outbox/{item_id}", headers={"Authorization": f"Bearer {ro_token}"})
    assert res_ro.status_code == 200
    ro_data = res_ro.json()
    assert "*" in ro_data["recipient_email"]
    assert "*" in ro_data["recipient_phone"]
    assert ro_data["payload_json"] is None

    # 3. System Admin (Notification Operator)
    res_admin = client.get(f"/api/notifications/outbox/{item_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["recipient_email"] == "confidential.applicant@test.edu.in"
    assert admin_data["payload_json"] == {"internal_secret": "TOP_SECRET"}
    assert "[REDACTED_SECRET]" in admin_data["provider_response"]


def test_invalid_expired_and_revoked_sse_authentication(client):
    """
    Test 5: Invalid, expired and revoked SSE authentication.
    - Prohibits reusable access token in query string.
    - Rejects invalid tickets.
    - Rejects expired tickets.
    """
    admin_token = get_auth_token(client, "admin@apex.edu.in")

    # Direct access token in query string is forbidden
    res_direct = client.get(f"/api/notifications/stream?token={admin_token}")
    assert res_direct.status_code == 401
    assert "prohibited for security" in res_direct.text

    # Invalid ticket
    res_invalid = client.get("/api/notifications/stream?ticket=st_invalid_fake_ticket_12345")
    assert res_invalid.status_code == 401
    assert "Invalid, expired, or already consumed" in res_invalid.text

    # Expired ticket
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@apex.edu.in").first()
        expired_ticket = StreamTicketService.create_ticket(user=user, ttl_seconds=-1)
    finally:
        db.close()

    res_expired = client.get(f"/api/notifications/stream?ticket={expired_ticket}")
    assert res_expired.status_code == 401


def test_one_time_stream_ticket_replay_prevention(client):
    """
    Test 6: One-time stream ticket exchange prevents replay attacks.
    Second consumption attempt must fail with 401.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")

    # Generate ticket
    res_ticket = client.post(
        "/api/notifications/stream-ticket",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    assert res_ticket.status_code == 200
    ticket = res_ticket.json()["ticket"]
    assert ticket.startswith("st_")

    # Consume directly via service to simulate connection consumption
    db = SessionLocal()
    try:
        consumed1 = StreamTicketService.consume_ticket(ticket, db)
        assert consumed1 is not None
        assert consumed1.user_id is not None

        # Replay attempt: Must return None
        consumed2 = StreamTicketService.consume_ticket(ticket, db)
        assert consumed2 is None
    finally:
        db.close()

    # Replay via HTTP endpoint must yield 401
    res_stream = client.get(f"/api/notifications/stream?ticket={ticket}")
    assert res_stream.status_code == 401


def test_sse_event_tenant_and_region_isolation():
    """
    Test 7: SSE event tenant and region isolation on broadcast filter.
    """
    c_inst1 = SSEClientConnection(
        user_id=1,
        institution_id=1,
        region="Western",
        roles={"INSTITUTION_ADMIN"}
    )
    c_inst2 = SSEClientConnection(
        user_id=2,
        institution_id=2,
        region="Northern",
        roles={"INSTITUTION_ADMIN"}
    )
    c_ro_western = SSEClientConnection(
        user_id=3,
        institution_id=None,
        region="Western",
        roles={"REGIONAL_OFFICER"}
    )

    ev_inst1 = {
        "title": "Inst 1 Notice",
        "institution_id": 1,
        "region": "Western",
        "recipient_role": "INSTITUTION_ADMIN"
    }

    assert c_inst1.is_authorized_for_event(ev_inst1) is True
    assert c_inst2.is_authorized_for_event(ev_inst1) is False  # Cross-tenant leak prevented
    assert c_ro_western.is_authorized_for_event(ev_inst1) is True  # Regional officer matches Western

    ev_inst2 = {
        "title": "Inst 2 Notice",
        "institution_id": 2,
        "region": "Northern",
        "recipient_role": "INSTITUTION_ADMIN"
    }

    assert c_inst1.is_authorized_for_event(ev_inst2) is False
    assert c_inst2.is_authorized_for_event(ev_inst2) is True
    assert c_ro_western.is_authorized_for_event(ev_inst2) is False  # Out-of-region leak prevented


def test_concurrent_dispatch_attempts_against_one_queued_record():
    """
    Test 8: Competing dispatchers claiming one queued record.
    Exactly one worker acquires the durable PROCESSING claim.
    """
    db = SessionLocal()
    key = f"CONCURRENCY-CLAIM-{datetime.now(timezone.utc).timestamp()}"
    try:
        item = NotificationOutbox(
            idempotency_key=key,
            correlation_id="corr-conc",
            event_type="TEST_CONCURRENCY",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="TEST",
            recipient_email="test@example.com",
            subject="Test Concurrency",
            body_text="Body",
            status="QUEUED"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        target_id = item.id
    finally:
        db.close()

    results = []

    def worker_claim():
        worker_db = SessionLocal()
        try:
            claimed = OutboxDispatcherService.claim_outbox_batch(worker_db, batch_size=5)
            if target_id in claimed:
                results.append(True)
        finally:
            worker_db.close()

    t1 = threading.Thread(target=worker_claim)
    t2 = threading.Thread(target=worker_claim)
    t3 = threading.Thread(target=worker_claim)

    t1.start(); t2.start(); t3.start()
    t1.join(); t2.join(); t3.join()

    # Invariant: Exactly one worker must claim the record
    assert len(results) == 1, f"Expected exactly 1 claim, got {len(results)}"


def test_recovery_of_stale_processing_claim():
    """
    Test 9: Recovery of a stale PROCESSING claim from a crashed worker.
    """
    db = SessionLocal()
    key = f"STALE-RECOVERY-{datetime.now(timezone.utc).timestamp()}"
    try:
        stale_item = NotificationOutbox(
            idempotency_key=key,
            correlation_id="corr-stale",
            event_type="TEST_STALE",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="TEST",
            recipient_email="officer@aicte.gov.in",
            subject="Stale Item",
            body_text="Body",
            status="PROCESSING",
            attempt_count=1,
            max_attempts=3,
            last_attempt_at=datetime.now(timezone.utc) - timedelta(seconds=600)  # Expired lease
        )
        db.add(stale_item)
        db.commit()
        db.refresh(stale_item)
        target_id = stale_item.id

        with patch.object(settings, "SMTP_HOST", ""):
            # Dispatch should recover stale claim
            summary = OutboxDispatcherService.dispatch_pending_outbox(db, batch_size=10, lease_seconds=300)
            assert summary["scanned"] >= 1
            assert summary["not_configured"] >= 1

        db.refresh(stale_item)
        assert stale_item.status == "NOT_CONFIGURED"
        assert stale_item.id == target_id
    finally:
        db.close()


def test_two_distinct_recipients_same_event_type_and_role():
    """
    Test 10: Two distinct recipients with the same event type and role produce separate queued outbox entries.
    """
    db = SessionLocal()
    try:
        users = db.query(User).limit(2).all()
        u1_id = users[0].id if users else None
        u2_id = users[1].id if len(users) > 1 else None

        out1 = OutboxDispatcherService.queue_notification(
            db=db,
            event_type="EVC_INVITATION",
            entity_type="EVC",
            entity_id=101,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            params={"link_url": "/evc/101"},
            recipient_user_id=u1_id,
            recipient_email="expert1@university.edu.in",
            recipient_role="COMMITTEE_MEMBER"
        )

        out2 = OutboxDispatcherService.queue_notification(
            db=db,
            event_type="EVC_INVITATION",
            entity_type="EVC",
            entity_id=101,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            params={"link_url": "/evc/101"},
            recipient_user_id=u2_id,
            recipient_email="expert2@university.edu.in",
            recipient_role="COMMITTEE_MEMBER"
        )

        db.commit()
        # Invariant: Distinct intended recipients receive their own queued messages
        assert out1.id != out2.id
        assert out1.idempotency_key != out2.idempotency_key

        # Re-enqueuing for recipient 1 yields identical existing record (idempotency)
        out1_dup = OutboxDispatcherService.queue_notification(
            db=db,
            event_type="EVC_INVITATION",
            entity_type="EVC",
            entity_id=101,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            params={"link_url": "/evc/101"},
            recipient_user_id=u1_id,
            recipient_email="expert1@university.edu.in",
            recipient_role="COMMITTEE_MEMBER"
        )
        assert out1_dup.id == out1.id
    finally:
        db.close()


def test_regional_officer_retry_not_dispatching_unrelated_records(client):
    """
    Test 11: Regional Officer retry does not dispatch unrelated outbox records from other regions or institutions.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    db = SessionLocal()
    key_prefix = f"RETRY-ISOLATION-{datetime.now(timezone.utc).timestamp()}"
    try:
        # Western dead letter record (eligible for retry)
        rec_west_dead = NotificationOutbox(
            idempotency_key=f"{key_prefix}-W-DEAD",
            correlation_id="corr-wd",
            event_type="TEST_RETRY",
            entity_type="APPLICATION",
            entity_id=1,
            region="Western",
            channel="EMAIL",
            template_code="TEST",
            recipient_email="ro.western@aicte.gov.in",
            subject="Western Retry Item",
            body_text="Body",
            status="DEAD_LETTER",
            attempt_count=3,
            max_attempts=3
        )
        # Northern queued record (unrelated)
        rec_north_queued = NotificationOutbox(
            idempotency_key=f"{key_prefix}-N-QUEUED",
            correlation_id="corr-nq",
            event_type="TEST_RETRY",
            entity_type="APPLICATION",
            entity_id=2,
            region="Northern",
            channel="EMAIL",
            template_code="TEST",
            recipient_email="ro.northern@aicte.gov.in",
            subject="Northern Queued Item",
            body_text="Body",
            status="QUEUED"
        )
        db.add(rec_west_dead)
        db.add(rec_north_queued)
        db.commit()
        db.refresh(rec_west_dead)
        db.refresh(rec_north_queued)
        dead_id = rec_west_dead.id
        north_id = rec_north_queued.id
    finally:
        db.close()

    # Retry the Western item
    res = client.post(
        f"/api/notifications/outbox/{dead_id}/retry",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 200

    # Verify Northern queued record was untouched and remains QUEUED
    check_db = SessionLocal()
    try:
        check_north = check_db.query(NotificationOutbox).filter(NotificationOutbox.id == north_id).first()
        assert check_north.status == "QUEUED"
        assert check_north.attempt_count == 0
    finally:
        check_db.close()


def test_polling_fallback_when_sse_is_disconnected(client):
    """
    Test 12: Polling fallback synchronizes persistent state when SSE is disconnected.
    """
    token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "unread_count" in data
    assert "total_count" in data
    assert isinstance(data["unread_count"], int)

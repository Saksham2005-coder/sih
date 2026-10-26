import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import smtplib
import socket

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.notification_outbox import NotificationOutbox
from app.models.alert import Notification
from app.models.user import User
from app.services.notification.providers import (
    SMTPEmailProvider,
    SMSProvider,
    ProviderResult,
    get_email_provider,
    get_sms_provider,
)
from app.services.notification.templates import NotificationTemplateEngine
from app.services.notification.outbox_dispatcher import OutboxDispatcherService
from app.services.notification.sse_broker import get_sse_broker, SSEClientConnection
from app.services.deadline_service import DeadlineService


def get_auth_token(client, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_notification_outbox_model_and_idempotency_constraint():
    """
    Test 1: Direct DB insertion of NotificationOutbox with idempotency constraint verification.
    """
    db = SessionLocal()
    unique_key = f"OUTBOX:TEST:{datetime.now(timezone.utc).timestamp()}"
    try:
        item1 = NotificationOutbox(
            idempotency_key=unique_key,
            correlation_id="corr-123",
            event_type="APPLICATION_SUBMITTED",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            recipient_email="admin@apex.edu.in",
            institution_id=1,
            region="Western",
            subject="Application Submission Acknowledgement",
            body_text="Your application has been received.",
            status="QUEUED",
        )
        db.add(item1)
        db.commit()
        db.refresh(item1)

        assert item1.id is not None
        assert item1.status == "QUEUED"
        assert item1.attempt_count == 0
        assert item1.created_at is not None

        # Verify idempotency constraint raises integrity error on duplicate
        item2 = NotificationOutbox(
            idempotency_key=unique_key,
            correlation_id="corr-456",
            event_type="APPLICATION_SUBMITTED",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="STAGE_SUBMITTED",
            recipient_email="admin@apex.edu.in",
            subject="Duplicate",
            body_text="Duplicate",
            status="QUEUED",
        )
        db.add(item2)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    finally:
        db.close()


def test_smtp_email_provider_unconfigured():
    """
    Test 2: SMTPEmailProvider returns NOT_CONFIGURED when SMTP_HOST is None, without throwing uncaught exceptions.
    """
    with patch.object(settings, "SMTP_HOST", ""):
        provider = SMTPEmailProvider()
        res = provider.send(
            recipient_email="test@example.com",
            recipient_phone=None,
            subject="Test Subject",
            body_text="Test Body",
        )
        assert isinstance(res, ProviderResult)
        assert res.status == "NOT_CONFIGURED"
        assert res.error_category == "CONFIGURATION_MISSING"
        assert "not configured" in res.response_message.lower()


def test_smtp_email_provider_mock_smtp_acceptance():
    """
    Test 3: SMTPEmailProvider sends email over SMTP and correctly returns ACCEPTED_BY_PROVIDER
    (distinguishing relay acceptance from recipient delivery).
    """
    with patch.object(settings, "SMTP_HOST", "smtp.aicte-test.local"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USER", "relay_user"), \
         patch.object(settings, "SMTP_PASSWORD", "secret_pass"), \
         patch.object(settings, "SMTP_USE_TLS", True):

        provider = SMTPEmailProvider()

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_server = MagicMock()
            mock_server.starttls.return_value = (220, b"Ready to start TLS")
            mock_server.login.return_value = (235, b"Authentication successful")
            mock_server.sendmail.return_value = {}  # Empty dict indicates all recipients accepted
            mock_smtp_class.return_value = mock_server

            res = provider.send(
                recipient_email="officer@aicte.gov.in",
                recipient_phone=None,
                subject="Urgent Scrutiny Due",
                body_text="Please scrutinize application APP-2026-001 within 48 hours.",
                body_html="<p>Please scrutinize application APP-2026-001 within 48 hours.</p>",
                metadata={"correlation_id": "corr-test-999"},
            )

            assert res.status == "ACCEPTED_BY_PROVIDER"
            assert res.provider_message_id is not None
            assert res.error_category is None
            assert mock_server.starttls.called
            assert mock_server.login.called
            assert mock_server.sendmail.called


def test_smtp_email_provider_timeout_and_error():
    """
    Test 4: SMTPEmailProvider handles connection failures and timeouts safely with proper error categorization.
    """
    with patch.object(settings, "SMTP_HOST", "smtp.aicte-test.local"), \
         patch.object(settings, "SMTP_PORT", 587):

        provider = SMTPEmailProvider()

        with patch("smtplib.SMTP", side_effect=socket.timeout("Connection timed out")):
            res = provider.send(
                recipient_email="officer@aicte.gov.in",
                recipient_phone=None,
                subject="Test",
                body_text="Test",
            )
            assert res.status == "RETRY_SCHEDULED"
            assert res.error_category == "TIMEOUT"
            assert "timed out" in res.error_message.lower()


def test_sms_provider_boundary_and_disclaimer():
    """
    Test 5: SMSProvider boundary marks messages as NOT_CONFIGURED or SIMULATED, never claiming false carrier delivery.
    """
    # Unconfigured provider
    with patch.object(settings, "SMS_GATEWAY_URL", ""), \
         patch.object(settings, "SMS_GATEWAY_API_KEY", ""):
        provider_unconfigured = SMSProvider()
        res_unconfigured = provider_unconfigured.send(
            recipient_email=None,
            recipient_phone="+919876543210",
            subject="AICTE SMS",
            body_text="AICTE Alert: Scrutiny pending.",
        )
        assert res_unconfigured.status in ["NOT_CONFIGURED", "SIMULATED"]
        assert res_unconfigured.error_category in ["CONFIGURATION_MISSING", None]

    # Gateway configured with URL
    with patch.object(settings, "SMS_GATEWAY_URL", "https://sms-mock.aicte.gov.in/api/v1/dispatch"), \
         patch.object(settings, "SMS_GATEWAY_API_KEY", "mock_key"), \
         patch.object(settings, "SMS_SENDER_ID", "AICTEN"):
        provider_simulated = SMSProvider()
        res_simulated = provider_simulated.send(
            recipient_email=None,
            recipient_phone="+919876543210",
            subject="AICTE SMS",
            body_text="AICTE Alert: Scrutiny pending.",
            metadata={"correlation_id": "sms-corr-1"},
        )
        assert res_simulated.status in ["SIMULATED", "ACCEPTED_BY_PROVIDER"]
        assert res_simulated.provider_message_id is not None


def test_notification_template_engine_rendering():
    """
    Test 6: NotificationTemplateEngine renders approved templates with safe links and accurate variable substitution.
    """
    subject, body_text, body_html = NotificationTemplateEngine.render(
        template_code="DEFICIENCY_COMMUNICATED",
        params={
            "institution_name": "Apex Institute of Technology & Management",
            "app_num": "AICTE-2026-EOA-98124",
            "category": "EOA_ANNUAL",
            "summary": "Building stability certificate unverified",
            "deadline": "30-Nov-2026",
            "link_url": "/applications/1",
        }
    )

    assert "AICTE-2026-EOA-98124" in subject
    assert "Deficiency Communicated" in subject
    assert "30-Nov-2026" in body_text
    assert "/applications/1" in body_text
    assert "<html" in body_html.lower()
    assert "AICTE-2026-EOA-98124" in body_html


def test_outbox_queue_deduplication():
    """
    Test 7: OutboxDispatcherService.queue_notification prevents duplicate outbox queuing with the same idempotency key.
    """
    db = SessionLocal()
    key = f"IDEMP-TEST-{datetime.now(timezone.utc).timestamp()}"
    try:
        out1 = OutboxDispatcherService.queue_notification(
            db=db,
            idempotency_key=key,
            event_type="SLA_WARNING",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="SLA_WARNING",
            params={
                "app_num": "AICTE-2026-EOA-98124",
                "institution_name": "Apex Institute",
                "region": "Western",
                "days_remaining": 3,
                "deadline": "01-Nov-2026",
                "link_url": "/applications/1"
            },
            recipient_email="bo.approval@aicte.gov.in",
            institution_id=1,
            region="Western",
        )
        db.commit()

        # Queue again with the exact same key
        out2 = OutboxDispatcherService.queue_notification(
            db=db,
            idempotency_key=key,
            event_type="SLA_WARNING",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="SLA_WARNING",
            params={
                "app_num": "AICTE-2026-EOA-98124",
                "institution_name": "Apex Institute",
                "region": "Western",
                "days_remaining": 3,
                "deadline": "01-Nov-2026",
                "link_url": "/applications/1"
            },
            recipient_email="bo.approval@aicte.gov.in",
            institution_id=1,
            region="Western",
        )
        db.commit()

        assert out1.id == out2.id
        # Check that exactly 1 outbox item exists for this key
        count = db.query(NotificationOutbox).filter(NotificationOutbox.idempotency_key == key).count()
        assert count == 1
    finally:
        db.close()


def test_outbox_dispatcher_exponential_backoff_and_dead_letter():
    """
    Test 8: Outbox dispatcher enforces bounded exponential backoff on retries and transitions to DEAD_LETTER after max attempts.
    """
    db = SessionLocal()
    key = f"RETRY-TEST-{datetime.now(timezone.utc).timestamp()}"
    try:
        outbox = NotificationOutbox(
            idempotency_key=key,
            correlation_id="corr-retry",
            event_type="TEST_EVENT",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="TEST_TEMPLATE",
            recipient_email="fail@test.com",
            subject="Test Failure",
            body_text="Body",
            status="QUEUED",
            attempt_count=0,
            max_attempts=3,
        )
        db.add(outbox)
        db.commit()
        db.refresh(outbox)

        # Mock email provider returning failure
        with patch.object(
            SMTPEmailProvider,
            "send",
            return_value=ProviderResult(status="FAILED", error_category="TIMEOUT", error_message="Connection timed out")
        ):
            # Attempt 1: Should set status RETRY_SCHEDULED, attempt_count=1, next_retry_at > now
            result1 = OutboxDispatcherService.dispatch_outbox_item(db, outbox)
            assert result1.status == "RETRY_SCHEDULED"
            assert result1.attempt_count == 1
            assert result1.next_retry_at is not None
            assert result1.last_error_category == "TIMEOUT"

            # Attempt 2
            outbox.next_retry_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            result2 = OutboxDispatcherService.dispatch_outbox_item(db, outbox)
            assert result2.status == "RETRY_SCHEDULED"
            assert result2.attempt_count == 2

            # Attempt 3: Exceeds max_attempts (3) -> DEAD_LETTER
            outbox.next_retry_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            result3 = OutboxDispatcherService.dispatch_outbox_item(db, outbox)
            assert result3.status == "DEAD_LETTER"
            assert result3.attempt_count == 3
            assert "terminal" in result3.last_error_message.lower()

    finally:
        db.close()


def test_manual_retry_outbox_item_endpoint(client):
    """
    Test 9: Authorized officer can manually retry a DEAD_LETTER outbox item via POST /api/notifications/outbox/{id}/retry.
    """
    ro_token = get_auth_token(client, "ro.western@aicte.gov.in")
    db = SessionLocal()
    key = f"MANUAL-RETRY-{datetime.now(timezone.utc).timestamp()}"
    try:
        dead_item = NotificationOutbox(
            idempotency_key=key,
            correlation_id="corr-dead",
            event_type="DEAD_LETTER_EVENT",
            entity_type="APPLICATION",
            entity_id=1,
            channel="EMAIL",
            template_code="TEST",
            recipient_email="officer@aicte.gov.in",
            subject="Dead Letter Item",
            body_text="Failed previously",
            status="DEAD_LETTER",
            attempt_count=3,
            max_attempts=3,
            region="Western",
        )
        db.add(dead_item)
        db.commit()
        db.refresh(dead_item)
        dead_id = dead_item.id
    finally:
        db.close()

    res = client.post(
        f"/api/notifications/outbox/{dead_id}/retry",
        headers={"Authorization": f"Bearer {ro_token}"},
    )
    assert res.status_code == 200, f"Retry failed: {res.text}"
    data = res.json()
    assert data["status"] in ["QUEUED", "NOT_CONFIGURED", "ACCEPTED_BY_PROVIDER", "SIMULATED"]
    assert data["attempt_count"] in [0, 1]
    assert data["id"] == dead_id


def test_outbox_api_scoping_and_authorization(client):
    """
    Test 10: Multi-tenant and regional scoping on GET /api/notifications/outbox.
    - Institution user only sees their own tenancy outbox items.
    - Regional officer only sees items matching their jurisdiction.
    """
    inst_token = get_auth_token(client, "admin@apex.edu.in")
    ro_western_token = get_auth_token(client, "ro.western@aicte.gov.in")

    # Institution query
    res_inst = client.get(
        "/api/notifications/outbox",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert res_inst.status_code == 200
    inst_items = res_inst.json()
    for item in inst_items:
        assert item["institution_id"] == 1 or item["recipient_email"] == "admin@apex.edu.in"

    # Regional officer query
    res_ro = client.get(
        "/api/notifications/outbox",
        headers={"Authorization": f"Bearer {ro_western_token}"},
    )
    assert res_ro.status_code == 200
    ro_items = res_ro.json()
    for item in ro_items:
        if item["region"]:
            assert item["region"].lower() == "western"


def test_channel_status_endpoint(client):
    """
    Test 11: GET /api/notifications/channels/status returns delivery channel health without leaking secrets.
    """
    token = get_auth_token(client, "sysadmin@aicte.gov.in")
    res = client.get(
        "/api/notifications/channels/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "channels" in data
    channel_names = [c["channel"] for c in data["channels"]]
    assert "EMAIL" in channel_names
    assert "SMS" in channel_names
    assert "SSE_STREAM" in channel_names
    # Verify no passwords or private keys are present
    raw_str = res.text.lower()
    assert "secret_password" not in raw_str
    assert "secret_key" not in raw_str


def test_unread_count_polling_endpoint(client):
    """
    Test 12: GET /api/notifications/unread-count returns accurate count for the authenticated user.
    """
    token = get_auth_token(client, "admin@apex.edu.in")
    res = client.get(
        "/api/notifications/unread-count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "unread_count" in data
    assert isinstance(data["unread_count"], int)
    assert "total_count" in data


def test_repeated_deadline_scan_zero_duplicate_outbox():
    """
    Test 13: Verifies that running repeated deadline scans does not create duplicate business notifications or duplicate outbox records.
    """
    db = SessionLocal()
    try:
        # Initial scan
        res1 = DeadlineService.run_deadline_and_escalation_scan(db, trigger_mode="MANUAL_TEST")
        initial_outbox_count = db.query(NotificationOutbox).count()

        # Immediate repeated scan
        res2 = DeadlineService.run_deadline_and_escalation_scan(db, trigger_mode="MANUAL_TEST")
        subsequent_outbox_count = db.query(NotificationOutbox).count()

        # Invariant: Idempotent scans must yield zero new outbox entries on repeat
        assert subsequent_outbox_count == initial_outbox_count, (
            f"Expected duplicate scan to create 0 new outbox entries, but count changed from {initial_outbox_count} to {subsequent_outbox_count}"
        )
    finally:
        db.close()

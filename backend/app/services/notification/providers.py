import smtplib
import socket
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderResult:
    """Standardized delivery result across all communication channels."""
    def __init__(
        self,
        status: str,
        provider_message_id: Optional[str] = None,
        response_message: str = "",
        error_category: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.status = status  # ACCEPTED_BY_PROVIDER, SIMULATED, NOT_CONFIGURED, RETRY_SCHEDULED, FAILED
        self.provider_message_id = provider_message_id
        self.response_message = response_message
        self.error_category = error_category
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "provider_message_id": self.provider_message_id,
            "response_message": self.response_message,
            "error_category": self.error_category,
            "error_message": self.error_message
        }


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(
        self,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProviderResult:
        """Dispatches notification via configured provider transport."""
        pass

    @abstractmethod
    def get_channel_status(self) -> Dict[str, Any]:
        """Returns truthful runtime provider configuration and availability state."""
        pass


class SMTPEmailProvider(BaseNotificationProvider):
    """
    Standard SMTP Email Delivery Provider.
    Supports TLS, SSL, plain authentication, custom ports (e.g. Mailpit 1025 or production 587).
    Fails closed or marks NOT_CONFIGURED when SMTP host is unconfigured.
    """

    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout = timeout_seconds

    def get_channel_status(self) -> Dict[str, Any]:
        is_configured = bool(settings.SMTP_HOST and settings.SMTP_HOST.strip())
        return {
            "channel": "EMAIL",
            "transport": "SMTP",
            "is_configured": is_configured,
            "host": settings.SMTP_HOST or "NOT_CONFIGURED",
            "port": settings.SMTP_PORT,
            "tls_enabled": settings.SMTP_USE_TLS,
            "sender": f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>",
            "status": "CONFIGURED" if is_configured else "NOT_CONFIGURED"
        }

    def send(
        self,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProviderResult:
        if not recipient_email or "@" not in recipient_email:
            return ProviderResult(
                status="FAILED",
                error_category="INVALID_RECIPIENT",
                error_message=f"Missing or invalid recipient email address: '{recipient_email}'"
            )

        if not settings.SMTP_HOST or not settings.SMTP_HOST.strip():
            # Honest reporting: Channel is not configured; do NOT pretend email was sent
            return ProviderResult(
                status="NOT_CONFIGURED",
                error_category="CONFIGURATION_MISSING",
                response_message="SMTP_HOST is not configured in environment. Outbox dispatch skipped without false delivery claim."
            )

        try:
            msg_id = make_msgid(domain="aicte.gov.in")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = recipient_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = msg_id
            msg["X-ReguFlow-Trace"] = (metadata or {}).get("correlation_id", "none")

            part_text = MIMEText(body_text, "plain", "utf-8")
            msg.attach(part_text)

            if body_html:
                part_html = MIMEText(body_html, "html", "utf-8")
                msg.attach(part_html)

            # Connect and transmit
            port = settings.SMTP_PORT
            if port == 465:
                # SSL direct
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=self.timeout)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=self.timeout)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM_EMAIL, [recipient_email], msg.as_string())
            server.quit()

            # Honest delivery assertion: Accepted by MTA relay
            return ProviderResult(
                status="ACCEPTED_BY_PROVIDER",
                provider_message_id=msg_id,
                response_message=f"250 Message queued on SMTP relay {settings.SMTP_HOST}:{port} for {recipient_email}"
            )

        except (socket.timeout, smtplib.SMTPConnectError) as e:
            return ProviderResult(
                status="RETRY_SCHEDULED",
                error_category="TIMEOUT",
                error_message=f"SMTP relay connection timed out ({settings.SMTP_HOST}:{settings.SMTP_PORT}): {str(e)}"
            )
        except smtplib.SMTPAuthenticationError as e:
            return ProviderResult(
                status="FAILED",
                error_category="AUTH_ERROR",
                error_message=f"SMTP authentication failure with user '{settings.SMTP_USER}': {str(e)}"
            )
        except smtplib.SMTPRecipientsRefused as e:
            return ProviderResult(
                status="FAILED",
                error_category="INVALID_RECIPIENT",
                error_message=f"Recipient refused by SMTP relay: {str(e)}"
            )
        except Exception as e:
            return ProviderResult(
                status="RETRY_SCHEDULED",
                error_category="NETWORK_ERROR",
                error_message=f"Transient SMTP error: {str(e)}"
            )


class SMSProvider(BaseNotificationProvider):
    """
    SMS Notification Provider Adapter.
    Boundary interface for future CDAC / NIC AICTE SMS Gateway integration.
    Until live gateway credentials are provided, marks NOT_CONFIGURED or SIMULATED.
    Never claims carrier delivery without live provider verification.
    """

    def get_channel_status(self) -> Dict[str, Any]:
        is_configured = bool(settings.SMS_GATEWAY_URL and settings.SMS_GATEWAY_API_KEY)
        return {
            "channel": "SMS",
            "transport": "CDAC_NIC_GATEWAY",
            "is_configured": is_configured,
            "gateway_url": settings.SMS_GATEWAY_URL or "NOT_CONFIGURED",
            "sender_id": settings.SMS_SENDER_ID,
            "status": "CONFIGURED" if is_configured else "SIMULATED_OR_NOT_CONFIGURED"
        }

    def send(
        self,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProviderResult:
        if not recipient_phone or len(recipient_phone.strip()) < 10:
            return ProviderResult(
                status="FAILED",
                error_category="INVALID_RECIPIENT",
                error_message=f"Missing or invalid recipient mobile phone number: '{recipient_phone}'"
            )

        meta = metadata or {}
        if not settings.SMS_GATEWAY_URL:
            # When gateway is unconfigured, record as SIMULATED in development / test mode
            # or NOT_CONFIGURED in production
            if getattr(settings, "DEMO_MODE", True):
                corr = str(meta.get("correlation_id", "0"))[:8]
                sim_msg_id = f"SIM-SMS-{meta.get('entity_id', '0')}-{corr}"
                return ProviderResult(
                    status="SIMULATED",
                    provider_message_id=sim_msg_id,
                    response_message=f"SMS payload simulated in sandbox mode (NIC gateway unconfigured). Recipient: {recipient_phone}."
                )
            return ProviderResult(
                status="NOT_CONFIGURED",
                error_category="CONFIGURATION_MISSING",
                response_message="CDAC/NIC SMS Gateway endpoint and API key not configured in production environment."
            )

        # In development / sandbox with configured gateway, record as SIMULATED or ACCEPTED_BY_PROVIDER
        corr = str(meta.get("correlation_id", "0"))[:8]
        return ProviderResult(
            status="SIMULATED",
            provider_message_id=f"GATEWAY-SIM-{corr}",
            response_message=f"SMS accepted by sandbox gateway adapter ({settings.SMS_GATEWAY_URL}). Sender ID: {settings.SMS_SENDER_ID}."
        )


_email_provider: Optional[SMTPEmailProvider] = None
_sms_provider: Optional[SMSProvider] = None


def get_email_provider() -> SMTPEmailProvider:
    global _email_provider
    if _email_provider is None:
        _email_provider = SMTPEmailProvider()
    return _email_provider


def get_sms_provider() -> SMSProvider:
    global _sms_provider
    if _sms_provider is None:
        _sms_provider = SMSProvider()
    return _sms_provider

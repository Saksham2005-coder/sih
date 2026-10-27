import re
import hashlib
from typing import List, Optional, Set, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, literal
from fastapi import HTTPException, status

from app.models.user import User
from app.models.notification_outbox import NotificationOutbox
from app.models.evc import EVCInspection

SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?([^\"'\s,]+)[\"']?", re.IGNORECASE),
    re.compile(r"(secret[_-]?key|api[_-]?key|access[_-]?token)[\"']?\s*[:=]\s*[\"']?([^\"'\s,]+)[\"']?", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----", re.IGNORECASE),
]


def redact_sensitive_text(text: Optional[str]) -> Optional[str]:
    """Redacts passwords, tokens, API keys, and private keys from strings."""
    if not text:
        return text
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


def mask_email(email: Optional[str]) -> Optional[str]:
    """Masks email address for field-level privacy (e.g. j***e@domain.com)."""
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """Masks phone number (e.g. +91*****3210)."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 6:
        return "***"
    return f"+91*****{digits[-4:]}"


def build_canonical_recipient_id(
    recipient_user_id: Optional[int] = None,
    recipient_email: Optional[str] = None,
    recipient_phone: Optional[str] = None,
    recipient_role: Optional[str] = None
) -> str:
    """
    Computes a canonical recipient identity for idempotency keys without exposing raw PII.
    """
    if recipient_user_id:
        return f"UID:{recipient_user_id}"
    if recipient_email and recipient_email.strip():
        norm_email = recipient_email.strip().lower()
        digest = hashlib.sha256(norm_email.encode("utf-8")).hexdigest()[:16]
        return f"EMAIL_HASH:{digest}"
    if recipient_phone and recipient_phone.strip():
        norm_phone = re.sub(r"\D", "", recipient_phone.strip())
        digest = hashlib.sha256(norm_phone.encode("utf-8")).hexdigest()[:16]
        return f"PHONE_HASH:{digest}"
    if recipient_role and recipient_role.strip():
        return f"ROLE:{recipient_role.strip()}"
    return "BROADCAST"


class NotificationScopePolicy:
    """
    Centralized server-side authorization and scoping policy for the Notification Outbox.
    Ensures mathematical consistency between outbox list, summary, detail, and retry operations.
    """

    @classmethod
    def get_user_roles(cls, user: User) -> Set[str]:
        return {r.role for r in user.roles}

    @classmethod
    def is_notification_operator(cls, user: User) -> bool:
        roles = cls.get_user_roles(user)
        return any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER"] for r in roles)

    @classmethod
    def is_statutory_executive(cls, user: User) -> bool:
        roles = cls.get_user_roles(user)
        return "COMPETENT_AUTHORITY" in roles

    @classmethod
    def is_operational_officer(cls, user: User) -> bool:
        roles = cls.get_user_roles(user)
        return any(r in ["REGIONAL_OFFICER", "EVC_COORDINATOR", "COMMITTEE_MEMBER"] for r in roles)

    @classmethod
    def apply_outbox_scope(cls, query, user: User, db: Session):
        """
        Applies strict jurisdictional and tenant filter constraints to an outbox query.
        Fails closed on missing required jurisdiction parameters.
        """
        user_roles = cls.get_user_roles(user)

        # 1. Platform Operators & National Authorities: System Admin, Bureau Officer, Competent Authority
        if any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
            return query

        # 2. Regional Officers: Strictly scoped to assigned region.
        # Missing jurisdiction information MUST FAIL CLOSED.
        if "REGIONAL_OFFICER" in user_roles:
            if not user.region or not user.region.strip():
                # Fail closed: No region assigned means zero access to regional records
                return query.filter(literal(False))
            assigned_region = user.region.strip().lower()
            return query.filter(
                NotificationOutbox.region != None,
                func.lower(NotificationOutbox.region) == assigned_region
            )

        # 3. EVC Coordinators: Scoped to EVC assignments and permitted region.
        if "EVC_COORDINATOR" in user_roles:
            if not user.region or not user.region.strip():
                return query.filter(literal(False))
            assigned_region = user.region.strip().lower()
            evc_conditions = or_(
                NotificationOutbox.recipient_role == "EVC_COORDINATOR",
                NotificationOutbox.recipient_user_id == user.id,
                NotificationOutbox.event_type.like("%EVC%"),
                NotificationOutbox.entity_type.in_(["EVC", "EVC_INSPECTION"])
            )
            return query.filter(
                NotificationOutbox.region != None,
                func.lower(NotificationOutbox.region) == assigned_region,
                evc_conditions
            )

        # 4. Committee Members: Scoped strictly to authorized case panel assignments.
        if "COMMITTEE_MEMBER" in user_roles:
            assigned_evc_rows = db.query(EVCInspection.id, EVCInspection.application_id).filter(
                or_(
                    EVCInspection.convener_user_id == user.id,
                    EVCInspection.expert_user_id == user.id,
                    EVCInspection.completed_by_id == user.id
                )
            ).all()
            assigned_app_ids = [r.application_id for r in assigned_evc_rows if r.application_id]
            assigned_evc_ids = [r.id for r in assigned_evc_rows if r.id]

            case_assignment_conditions = []
            if assigned_app_ids:
                case_assignment_conditions.append(
                    and_(
                        NotificationOutbox.entity_type == "APPLICATION",
                        NotificationOutbox.entity_id.in_(assigned_app_ids)
                    )
                )
            if assigned_evc_ids:
                case_assignment_conditions.append(
                    and_(
                        NotificationOutbox.entity_type.in_(["EVC", "EVC_INSPECTION"]),
                        NotificationOutbox.entity_id.in_(assigned_evc_ids)
                    )
                )

            # Direct recipient check MUST also relate to authorized committee role or assignment
            direct_match = and_(
                NotificationOutbox.recipient_user_id == user.id,
                NotificationOutbox.recipient_role == "COMMITTEE_MEMBER"
            )

            if case_assignment_conditions:
                return query.filter(
                    or_(
                        direct_match,
                        and_(
                            NotificationOutbox.recipient_role == "COMMITTEE_MEMBER",
                            or_(*case_assignment_conditions)
                        )
                    )
                )
            else:
                return query.filter(direct_match)

        # 5. Institution Users: Scoped strictly to their own institution_id
        if not user.institution_id:
            # Non-officer without institution fails closed
            return query.filter(literal(False))

        # Direct recipient match cannot bypass institutional boundaries
        return query.filter(
            NotificationOutbox.institution_id == user.institution_id
        )

    @classmethod
    def verify_outbox_record_access(cls, item: NotificationOutbox, user: User, db: Session) -> None:
        """
        Validates entity-level access for outbox detail and retry endpoints.
        Enforces identical scoping constraints as the list endpoint.
        """
        user_roles = cls.get_user_roles(user)

        # National / Platform authorities
        if any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in user_roles):
            return

        # Regional Officer
        if "REGIONAL_OFFICER" in user_roles:
            if not user.region or not user.region.strip():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Regional Officer account has no assigned jurisdiction."
                )
            if not item.region or item.region.strip().lower() != user.region.strip().lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Record region '{item.region}' is outside your assigned region '{user.region}'."
                )
            return

        # EVC Coordinator
        if "EVC_COORDINATOR" in user_roles:
            if not user.region or not user.region.strip():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: EVC Coordinator account has no assigned jurisdiction."
                )
            if not item.region or item.region.strip().lower() != user.region.strip().lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Record region '{item.region}' is outside your assigned region '{user.region}'."
                )
            is_evc_event = (
                item.recipient_role == "EVC_COORDINATOR" or
                item.recipient_user_id == user.id or
                "EVC" in (item.event_type or "").upper() or
                item.entity_type in ["EVC", "EVC_INSPECTION"]
            )
            if not is_evc_event:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Record does not pertain to EVC coordination responsibilities."
                )
            return

        # Committee Member
        if "COMMITTEE_MEMBER" in user_roles:
            # Check direct recipient
            if item.recipient_user_id == user.id and item.recipient_role == "COMMITTEE_MEMBER":
                return

            assigned_evc_rows = db.query(EVCInspection.id, EVCInspection.application_id).filter(
                or_(
                    EVCInspection.convener_user_id == user.id,
                    EVCInspection.expert_user_id == user.id,
                    EVCInspection.completed_by_id == user.id
                )
            ).all()
            assigned_app_ids = {r.application_id for r in assigned_evc_rows if r.application_id}
            assigned_evc_ids = {r.id for r in assigned_evc_rows if r.id}

            is_assigned = (
                (item.entity_type == "APPLICATION" and item.entity_id in assigned_app_ids) or
                (item.entity_type in ["EVC", "EVC_INSPECTION"] and item.entity_id in assigned_evc_ids)
            )
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not assigned to the case associated with this notification."
                )
            return

        # Institution Users
        if not user.institution_id or item.institution_id != user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access notification outbox records of another institution."
            )

    @classmethod
    def transform_outbox_record(cls, item: NotificationOutbox, user: User) -> Dict[str, Any]:
        """
        Applies field-level disclosure rules based on caller's role.
        - Operators: full record with credential redaction.
        - Operational officers: masked recipient contact, sanitized provider diagnostics.
        - General users: only essential notification experience fields.
        """
        user_roles = cls.get_user_roles(user)
        is_operator = any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER"] for r in user_roles)
        is_executive = "COMPETENT_AUTHORITY" in user_roles
        is_operational = any(r in ["REGIONAL_OFFICER", "EVC_COORDINATOR", "COMMITTEE_MEMBER"] for r in user_roles)

        # Baseline dictionary
        data: Dict[str, Any] = {
            "id": item.id,
            "idempotency_key": item.idempotency_key,
            "correlation_id": item.correlation_id,
            "event_type": item.event_type,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "institution_id": item.institution_id,
            "region": item.region,
            "recipient_role": item.recipient_role,
            "recipient_user_id": item.recipient_user_id,
            "recipient_email": None,
            "recipient_phone": None,
            "channel": item.channel,
            "template_code": item.template_code,
            "subject": redact_sensitive_text(item.subject),
            "body_text": redact_sensitive_text(item.body_text),
            "body_html": redact_sensitive_text(item.body_html),
            "link_url": item.link_url,
            "status": item.status,
            "attempt_count": item.attempt_count,
            "max_attempts": item.max_attempts,
            "next_retry_at": item.next_retry_at,
            "last_attempt_at": item.last_attempt_at,
            "last_error_category": None,
            "last_error_message": None,
            "provider_message_id": None,
            "provider_response": None,
            "payload_json": None,
            "sent_at": item.sent_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

        if is_operator or is_executive:
            # Full operational transparency for operators
            data["recipient_email"] = item.recipient_email
            data["recipient_phone"] = item.recipient_phone
            data["last_error_category"] = item.last_error_category
            data["last_error_message"] = redact_sensitive_text(item.last_error_message)
            data["provider_message_id"] = item.provider_message_id
            data["provider_response"] = redact_sensitive_text(item.provider_response)
            data["payload_json"] = item.payload_json
        elif is_operational:
            # Operational triage info with masked recipient contact and safe diagnostics
            data["recipient_email"] = mask_email(item.recipient_email)
            data["recipient_phone"] = mask_phone(item.recipient_phone)
            data["last_error_category"] = item.last_error_category
            data["last_error_message"] = (
                f"Delivery Error: {item.last_error_category}" if item.last_error_category else None
            )
            data["provider_message_id"] = item.provider_message_id
            # Provider response masked to prevent leaking server IPs or auth tokens
            data["provider_response"] = "Provider response recorded." if item.provider_response else None
        else:
            # General institutional users receive only notification experience fields
            data["idempotency_key"] = "[PROTECTED]"
            data["correlation_id"] = "[PROTECTED]"
            data["recipient_email"] = mask_email(item.recipient_email)
            data["attempt_count"] = 0
            data["max_attempts"] = 0
            data["next_retry_at"] = None
            data["last_attempt_at"] = None

        return data

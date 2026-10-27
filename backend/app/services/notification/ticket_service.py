import secrets
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Set, Dict
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.token_blacklist import RevokedToken


@dataclass
class StreamTicket:
    ticket: str
    user_id: int
    institution_id: Optional[int]
    region: Optional[str]
    roles: Set[str]
    session_jti: Optional[str]
    created_at: datetime
    expires_at: datetime
    consumed: bool = False


class StreamTicketService:
    """
    Manages short-lived, single-use stream tickets for secure SSE stream establishment.
    Eliminates reusable JWT leakage in EventSource URLs and browser history.
    """
    _tickets: Dict[str, StreamTicket] = {}
    _lock = threading.Lock()

    @classmethod
    def create_ticket(
        cls,
        user: User,
        session_jti: Optional[str] = None,
        ttl_seconds: int = 45
    ) -> str:
        ticket_str = f"st_{secrets.token_urlsafe(32)}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        ticket_obj = StreamTicket(
            ticket=ticket_str,
            user_id=user.id,
            institution_id=user.institution_id,
            region=user.region,
            roles={r.role for r in user.roles},
            session_jti=session_jti,
            created_at=now,
            expires_at=expires_at,
            consumed=False
        )

        with cls._lock:
            # Prune expired tickets
            cls._prune_expired_locked(now)
            cls._tickets[ticket_str] = ticket_obj

        return ticket_str

    @classmethod
    def consume_ticket(cls, ticket_str: str, db: Session) -> Optional[StreamTicket]:
        """
        Atomically validates and consumes a ticket.
        Enforces one-time use, expiration, user activation, and JWT blacklist revocation.
        """
        now = datetime.now(timezone.utc)
        with cls._lock:
            ticket = cls._tickets.get(ticket_str)
            if not ticket:
                return None
            if ticket.consumed or now > ticket.expires_at:
                # Expired or already consumed
                cls._tickets.pop(ticket_str, None)
                return None
            # Atomically mark consumed and remove
            ticket.consumed = True
            cls._tickets.pop(ticket_str, None)

        # Revalidate JWT revocation if session_jti was bound
        if ticket.session_jti:
            revoked = db.query(RevokedToken).filter(RevokedToken.jti == ticket.session_jti).first()
            if revoked:
                return None

        # Revalidate user active state
        user = db.query(User).filter(User.id == ticket.user_id, User.is_active == True).first()
        if not user:
            return None

        return ticket

    @classmethod
    def _prune_expired_locked(cls, now: datetime):
        expired = [k for k, v in cls._tickets.items() if now > v.expires_at or v.consumed]
        for k in expired:
            cls._tickets.pop(k, None)

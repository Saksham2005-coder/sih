import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_current_user, require_roles
from app.core.security import decode_access_token
from app.models.user import User
from app.models.alert import Notification
from app.models.notification_outbox import NotificationOutbox
from app.models.token_blacklist import RevokedToken
from app.schemas.notification_outbox import (
    NotificationOutboxResponse,
    NotificationOutboxSummaryResponse,
    NotificationChannelStatusResponse,
    ChannelHealthStatus,
    NotificationUnreadCountResponse,
    StreamTicketResponse
)
from app.services.notification.providers import get_email_provider, get_sms_provider
from app.services.notification.outbox_dispatcher import OutboxDispatcherService
from app.services.notification.sse_broker import get_sse_broker, SSEClientConnection
from app.services.notification.auth_policy import NotificationScopePolicy
from app.services.notification.ticket_service import StreamTicketService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notification Outbox & Real-Time Delivery"])


@router.get("/outbox", response_model=List[NotificationOutboxResponse])
def get_notification_outbox(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves notification outbox records scoped strictly to caller's institutional or regional authority.
    Centralized server-side scoping policy enforces fail-closed jurisdiction checks.
    Field-level disclosure rules minimize sensitive contact information and provider diagnostics.
    """
    base_query = db.query(NotificationOutbox)
    query = NotificationScopePolicy.apply_outbox_scope(base_query, current_user, db)

    if status_filter:
        query = query.filter(NotificationOutbox.status == status_filter)
    if channel:
        query = query.filter(NotificationOutbox.channel == channel)
    if event_type:
        query = query.filter(NotificationOutbox.event_type == event_type)

    items = query.order_by(NotificationOutbox.created_at.desc()).limit(limit).all()
    return [NotificationScopePolicy.transform_outbox_record(item, current_user) for item in items]


@router.get("/outbox/summary", response_model=NotificationOutboxSummaryResponse)
def get_outbox_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggregated status counts across the transactional outbox.
    Uses identical scoped query as the outbox list endpoint for mathematical consistency.
    """
    base_query = db.query(NotificationOutbox)
    scoped_query = NotificationScopePolicy.apply_outbox_scope(base_query, current_user, db)
    items = scoped_query.all()

    summary = {
        "total": len(items),
        "queued": sum(1 for i in items if i.status == "QUEUED"),
        "processing": sum(1 for i in items if i.status == "PROCESSING"),
        "accepted_by_provider": sum(1 for i in items if i.status == "ACCEPTED_BY_PROVIDER"),
        "simulated": sum(1 for i in items if i.status == "SIMULATED"),
        "not_configured": sum(1 for i in items if i.status == "NOT_CONFIGURED"),
        "retry_scheduled": sum(1 for i in items if i.status == "RETRY_SCHEDULED"),
        "dead_letter": sum(1 for i in items if i.status == "DEAD_LETTER"),
        "failed": sum(1 for i in items if i.status == "FAILED"),
    }
    return NotificationOutboxSummaryResponse(**summary)


@router.get("/outbox/{id}", response_model=NotificationOutboxResponse)
def get_outbox_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detailed inspection of a specific outbox dispatch with diagnostic error history.
    Enforces identical jurisdictional and multi-tenant scoping policy as the list endpoint.
    """
    item = db.query(NotificationOutbox).filter(NotificationOutbox.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Outbox record not found")

    NotificationScopePolicy.verify_outbox_record_access(item, current_user, db)
    return NotificationScopePolicy.transform_outbox_record(item, current_user)


@router.post("/outbox/{id}/retry", response_model=NotificationOutboxResponse)
def retry_outbox_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER", "REGIONAL_OFFICER"]))
):
    """
    Manually re-enqueues a failed or dead-letter outbox dispatch for reprocessing.
    - Authorizes target record first via centralized scoping policy.
    - Regional Officers can only retry records within their regional jurisdiction.
    - Dispatches ONLY the target record without triggering unrelated batch items.
    - Preserves audit log with the actual acting role.
    """
    item = db.query(NotificationOutbox).filter(NotificationOutbox.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"NotificationOutbox #{id} not found")

    NotificationScopePolicy.verify_outbox_record_access(item, current_user, db)

    try:
        updated = OutboxDispatcherService.manual_retry(db=db, outbox_id=id, current_user=current_user)
        # Dispatch ONLY this authorized record immediately; do NOT touch unrelated dispatches
        OutboxDispatcherService.dispatch_single_item(db=db, outbox_id=id)
        db.refresh(updated)
        return NotificationScopePolicy.transform_outbox_record(updated, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/outbox/dispatch-now")
def trigger_outbox_dispatch(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER"]))
):
    """
    Triggers an on-demand batch run of the outbox dispatcher worker.
    Reserved exclusively for authorized operational roles (SYSTEM_ADMIN, BUREAU_OFFICER).
    """
    summary = OutboxDispatcherService.dispatch_pending_outbox(db=db, batch_size=50)
    return {"message": "Outbox dispatch cycle executed", "summary": summary}


@router.get("/channels/status", response_model=NotificationChannelStatusResponse)
def get_channel_status(
    current_user: User = Depends(get_current_user)
):
    """
    Returns truthful configuration and health status of all delivery channels (Email, SMS, In-App, SSE).
    - Protects SMTP credentials, hostnames, and ports from ordinary users.
    - Transparently reports process-local asyncio broker scope and fallback polling synchronization.
    """
    email_prov = get_email_provider()
    sms_prov = get_sms_provider()
    sse_broker = get_sse_broker()

    email_status = email_prov.get_channel_status()
    sms_status = sms_prov.get_channel_status()

    is_operator = NotificationScopePolicy.is_notification_operator(current_user)

    # Protect SMTP configuration details from non-operator users
    if not is_operator:
        safe_email_details = {
            "channel": "EMAIL",
            "transport": "SMTP",
            "is_configured": email_status["is_configured"],
            "status": email_status["status"]
        }
        safe_sms_details = {
            "channel": "SMS",
            "transport": sms_status["transport"],
            "is_configured": sms_status["is_configured"],
            "status": sms_status["status"]
        }
    else:
        safe_email_details = email_status
        safe_sms_details = sms_status

    channels = [
        ChannelHealthStatus(
            channel="EMAIL",
            transport=email_status["transport"],
            is_configured=email_status["is_configured"],
            status=email_status["status"],
            details=safe_email_details
        ),
        ChannelHealthStatus(
            channel="SMS",
            transport=sms_status["transport"],
            is_configured=sms_status["is_configured"],
            status=sms_status["status"],
            details=safe_sms_details
        ),
        ChannelHealthStatus(
            channel="IN_APP",
            transport="POSTGRES_SQLITE_RELATIONAL",
            is_configured=True,
            status="ACTIVE",
            details={"storage": "notifications table", "query_supported": True}
        ),
        ChannelHealthStatus(
            channel="SSE_STREAM",
            transport="ASYNCIO_PUB_SUB",
            is_configured=True,
            status="ACTIVE",
            details={
                "active_subscribers": sse_broker.get_active_clients_count(),
                "broker_architecture": "PROCESS_LOCAL_ASYNCIO",
                "single_process_scope": True,
                "multi_worker_fallback": "DB_POLLING"
            }
        )
    ]

    return NotificationChannelStatusResponse(
        channels=channels,
        active_sse_subscribers=sse_broker.get_active_clients_count()
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fast count of unread notifications for navigation badge and polling fallback."""
    query = db.query(Notification)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if not current_user.institution_id:
            return NotificationUnreadCountResponse(unread_count=0, total_count=0)
        query = query.filter(
            or_(
                Notification.institution_id == current_user.institution_id,
                Notification.user_id == current_user.id
            )
        )
    elif "REGIONAL_OFFICER" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER"] for r in user_roles):
        if not current_user.region:
            return NotificationUnreadCountResponse(unread_count=0, total_count=0)
        query = query.filter(
            or_(
                Notification.user_id == current_user.id,
                Notification.recipient_role == "REGIONAL_OFFICER"
            )
        )
    else:
        conditions = [
            Notification.user_id == current_user.id,
            Notification.recipient_role.in_(user_roles),
            (Notification.institution_id == None) & (Notification.recipient_role == None)
        ]
        query = query.filter(or_(*conditions))

    total = query.count()
    unread = query.filter(Notification.is_read == False).count()
    return NotificationUnreadCountResponse(unread_count=unread, total_count=total)


@router.post("/stream-ticket", response_model=StreamTicketResponse)
def create_stream_ticket(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Generates a secure, short-lived, single-use stream ticket for EventSource establishment.
    Eliminates reusable JWT leakage in EventSource URLs and browser history.
    Ticket is bound to caller's session, expires in 45 seconds, and is atomically consumed.
    """
    auth_header = request.headers.get("Authorization")
    session_jti = None
    if auth_header and auth_header.startswith("Bearer "):
        token_str = auth_header.split(" ")[1]
        payload = decode_access_token(token_str)
        if payload:
            session_jti = payload.get("jti")

    ticket = StreamTicketService.create_ticket(
        user=current_user,
        session_jti=session_jti,
        ttl_seconds=45
    )
    return StreamTicketResponse(ticket=ticket, expires_in_seconds=45)


@router.get("/stream")
async def sse_notification_stream(
    request: Request,
    ticket: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Authenticated Server-Sent Events (SSE) stream for live in-app notifications and operational updates.
    - Prohibits reusable access token in query string (fails closed with HTTP 401).
    - Authenticates via single-use stream ticket or Authorization header.
    - Enforces tenant and regional jurisdictional boundaries on broadcast events.
    - Periodically revalidates session status against token blacklists and active user flags.
    - Sends 15-second heartbeats and gracefully releases connections upon client disconnect.
    """
    # Security Rule: Reusable access tokens in query parameters are strictly forbidden
    if token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Direct access token in query string is prohibited for security. Use Authorization header or request a single-use stream ticket via POST /api/notifications/stream-ticket."
        )

    user_id = None
    user_institution_id = None
    user_region = None
    user_roles = set()
    user_full_name = "User"
    session_jti = None

    if ticket:
        ticket_data = StreamTicketService.consume_ticket(ticket, db)
        if not ticket_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or already consumed stream ticket."
            )
        user_id = ticket_data.user_id
        user_institution_id = ticket_data.institution_id
        user_region = ticket_data.region
        user_roles = ticket_data.roles
        session_jti = ticket_data.session_jti

        u = db.query(User).filter(User.id == user_id).first()
        if u:
            user_full_name = u.full_name
    else:
        # Authenticate via Authorization Bearer header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a valid stream ticket or Authorization Bearer header."
            )
        token_str = auth_header.split(" ")[1]
        payload = decode_access_token(token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")

        raw_sub = payload.get("user_id") or payload.get("sub")
        session_jti = payload.get("jti")
        if not raw_sub:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        # Check blacklist
        if session_jti:
            revoked = db.query(RevokedToken).filter(RevokedToken.jti == session_jti).first()
            if revoked:
                raise HTTPException(status_code=401, detail="Token has been revoked.")

        user = db.query(User).filter(or_(User.id == raw_sub, User.email == str(raw_sub)), User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found or inactive.")

        user_id = user.id
        user_institution_id = user.institution_id
        user_region = user.region
        user_roles = {r.role for r in user.roles}
        user_full_name = user.full_name

    client_conn = SSEClientConnection(
        user_id=user_id,
        institution_id=user_institution_id,
        region=user_region,
        roles=user_roles,
        queue_max_size=50
    )

    broker = get_sse_broker()
    await broker.register_client(client_conn)

    async def event_generator():
        last_session_check = datetime.now(timezone.utc)
        try:
            # Yield initial connection confirmation
            connect_payload = {
                "event_type": "CONNECTED",
                "message": f"Connected to ReguFlow 360 Live Event Stream as {user_full_name}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"event: connected\ndata: {json.dumps(connect_payload)}\n\n"

            while True:
                # Check client disconnect
                if await request.is_disconnected():
                    break

                # Periodic session revalidation (every 30 seconds)
                now = datetime.now(timezone.utc)
                if (now - last_session_check).total_seconds() > 30:
                    last_session_check = now
                    # Verify session revocation and user active state in fresh session
                    check_db = SessionLocal()
                    try:
                        u = check_db.query(User).filter(User.id == user_id, User.is_active == True).first()
                        if not u:
                            yield f"event: error\ndata: {{\"error\": \"User account deactivated\"}}\n\n"
                            break
                        if session_jti:
                            revoked = check_db.query(RevokedToken).filter(RevokedToken.jti == session_jti).first()
                            if revoked:
                                yield f"event: error\ndata: {{\"error\": \"Session revoked\"}}\n\n"
                                break
                    finally:
                        check_db.close()

                try:
                    event_data = await asyncio.wait_for(client_conn.queue.get(), timeout=15.0)
                    yield f"event: notification\ndata: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    yield f": ping - {datetime.now(timezone.utc).isoformat()}\n\n"
                except asyncio.CancelledError:
                    break

        finally:
            await broker.unregister_client(client_conn)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

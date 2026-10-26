import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import decode_access_token
from app.models.user import User
from app.models.alert import Notification
from app.models.notification_outbox import NotificationOutbox
from app.schemas.notification_outbox import (
    NotificationOutboxResponse,
    NotificationOutboxSummaryResponse,
    NotificationChannelStatusResponse,
    ChannelHealthStatus,
    NotificationUnreadCountResponse
)
from app.services.notification.providers import get_email_provider, get_sms_provider
from app.services.notification.outbox_dispatcher import OutboxDispatcherService
from app.services.notification.sse_broker import get_sse_broker, SSEClientConnection

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
    Administrative visibility into pending, delivered, retried, and dead-letter dispatches.
    """
    query = db.query(NotificationOutbox)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        # Institution users see only their institution outbox dispatches
        query = query.filter(NotificationOutbox.institution_id == current_user.institution_id)
    elif "SYSTEM_ADMIN" in user_roles or "BUREAU_OFFICER" in user_roles or "COMPETENT_AUTHORITY" in user_roles:
        # National officers can inspect all outbox dispatches
        pass
    elif "REGIONAL_OFFICER" in user_roles:
        # Regional officer strictly scoped to assigned region
        if current_user.region:
            query = query.filter(
                or_(
                    NotificationOutbox.region == current_user.region,
                    NotificationOutbox.region == None
                )
            )
    else:
        query = query.filter(NotificationOutbox.recipient_role.in_(user_roles))

    if status_filter:
        query = query.filter(NotificationOutbox.status == status_filter)
    if channel:
        query = query.filter(NotificationOutbox.channel == channel)
    if event_type:
        query = query.filter(NotificationOutbox.event_type == event_type)

    return query.order_by(NotificationOutbox.created_at.desc()).limit(limit).all()


@router.get("/outbox/summary", response_model=NotificationOutboxSummaryResponse)
def get_outbox_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregated status counts across the transactional outbox."""
    query = db.query(NotificationOutbox)
    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        query = query.filter(NotificationOutbox.institution_id == current_user.institution_id)
    elif "REGIONAL_OFFICER" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER"] for r in user_roles):
        if current_user.region:
            query = query.filter(or_(NotificationOutbox.region == current_user.region, NotificationOutbox.region == None))

    items = query.all()
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
    """Detailed inspection of a specific outbox dispatch with diagnostic error history."""
    item = db.query(NotificationOutbox).filter(NotificationOutbox.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Outbox record not found")

    user_roles = [r.role for r in current_user.roles]
    is_officer = any(r in [
        "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
        "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
    ] for r in user_roles)

    if not is_officer:
        if item.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access outbox dispatch of another institution")
    elif "REGIONAL_OFFICER" in user_roles and not any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER"] for r in user_roles):
        if item.region and current_user.region and item.region.lower() != current_user.region.lower():
            raise HTTPException(status_code=403, detail="Access denied: Outbox dispatch is registered outside your assigned region")

    return item


@router.post("/outbox/{id}/retry", response_model=NotificationOutboxResponse)
def retry_outbox_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER", "REGIONAL_OFFICER"]))
):
    """
    Manually re-enqueues a failed or dead-letter outbox dispatch for reprocessing.
    Allowed for System Administrator, Bureau Officer, and Regional Officers within their region.
    """
    item = db.query(NotificationOutbox).filter(NotificationOutbox.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"NotificationOutbox #{id} not found")

    user_roles = [r.role for r in current_user.roles]
    if "REGIONAL_OFFICER" in user_roles and "SYSTEM_ADMIN" not in user_roles and "BUREAU_OFFICER" not in user_roles:
        if item.region and current_user.region and item.region.lower() != current_user.region.lower():
            raise HTTPException(status_code=403, detail="Cannot retry outbox items outside your regional jurisdiction")

    try:
        updated = OutboxDispatcherService.manual_retry(db=db, outbox_id=id, current_user=current_user)
        # Attempt immediate dispatch
        OutboxDispatcherService.dispatch_pending_outbox(db=db, batch_size=10)
        db.refresh(updated)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/outbox/dispatch-now")
def trigger_outbox_dispatch(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SYSTEM_ADMIN", "BUREAU_OFFICER"]))
):
    """Triggers an on-demand batch run of the outbox dispatcher worker."""
    summary = OutboxDispatcherService.dispatch_pending_outbox(db=db, batch_size=50)
    return {"message": "Outbox dispatch cycle executed", "summary": summary}


@router.get("/channels/status", response_model=NotificationChannelStatusResponse)
def get_channel_status(
    current_user: User = Depends(get_current_user)
):
    """
    Returns truthful configuration and health status of all delivery channels (Email, SMS, In-App, SSE).
    Accurately identifies unconfigured channels without falsifying delivery capabilities.
    """
    email_prov = get_email_provider()
    sms_prov = get_sms_provider()
    sse_broker = get_sse_broker()

    email_status = email_prov.get_channel_status()
    sms_status = sms_prov.get_channel_status()

    channels = [
        ChannelHealthStatus(
            channel="EMAIL",
            transport=email_status["transport"],
            is_configured=email_status["is_configured"],
            status=email_status["status"],
            details=email_status
        ),
        ChannelHealthStatus(
            channel="SMS",
            transport=sms_status["transport"],
            is_configured=sms_status["is_configured"],
            status=sms_status["status"],
            details=sms_status
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
            details={"active_subscribers": sse_broker.get_active_clients_count()}
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
        query = query.filter(
            or_(
                Notification.institution_id == current_user.institution_id,
                Notification.user_id == current_user.id
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


@router.get("/stream")
async def sse_notification_stream(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Authenticated Server-Sent Events (SSE) stream for live in-app notifications and operational updates.
    Enforces user, tenant, and regional jurisdictional boundaries on broadcast events.
    Sends 15-second heartbeats and gracefully releases connections upon client disconnect.
    """
    # Authenticate via query param token or Authorization header
    auth_header = request.headers.get("Authorization")
    jwt_token = token
    if not jwt_token and auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header.split(" ")[1]

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token for SSE stream."
        )

    payload = decode_access_token(jwt_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    # Fetch user for scoping metadata
    user = db.query(User).filter(or_(User.id == user_id, User.email == str(user_id))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    user_roles = {r.role for r in user.roles}
    client_conn = SSEClientConnection(
        user_id=user.id,
        institution_id=user.institution_id,
        region=user.region,
        roles=user_roles,
        queue_max_size=50
    )

    broker = get_sse_broker()
    await broker.register_client(client_conn)

    async def event_generator():
        try:
            # Yield initial connection confirmation
            connect_payload = {
                "event_type": "CONNECTED",
                "message": f"Connected to ReguFlow 360 Live Event Stream as {user.full_name}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"event: connected\ndata: {json.dumps(connect_payload)}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event or 15s heartbeat
                    event_data = await asyncio.wait_for(client_conn.queue.get(), timeout=15.0)
                    yield f"event: notification\ndata: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep NAT/proxy connection alive
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

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SSEClientConnection:
    """Represents an active authenticated SSE client listener."""
    def __init__(
        self,
        user_id: int,
        institution_id: Optional[int],
        region: Optional[str],
        roles: Set[str],
        queue_max_size: int = 50
    ):
        self.user_id = user_id
        self.institution_id = institution_id
        self.region = region.lower() if region else None
        self.roles = set(roles or [])
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_max_size)
        self.connected_at = datetime.now(timezone.utc)
        self.is_active = True

    def is_authorized_for_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Enforces tenant, role, and regional jurisdictional boundaries on broadcast events.
        Never delivers private cross-tenant or out-of-region events to unauthorized listeners.
        """
        is_officer = any(r in [
            "REGIONAL_OFFICER", "BUREAU_OFFICER", "COMMITTEE_MEMBER",
            "EVC_COORDINATOR", "COMPETENT_AUTHORITY", "SYSTEM_ADMIN"
        ] for r in self.roles)

        target_user_id = event_data.get("recipient_user_id") or event_data.get("user_id")
        target_inst_id = event_data.get("institution_id")
        target_role = event_data.get("recipient_role")
        target_region = (event_data.get("region") or "").lower() or None

        # Direct user match
        if target_user_id is not None and target_user_id == self.user_id:
            return True

        if not is_officer:
            # Institution tenant boundary: strictly within self.institution_id
            if target_inst_id is not None and target_inst_id == self.institution_id:
                return True
            return False

        # National officer roles see all events
        if any(r in ["SYSTEM_ADMIN", "BUREAU_OFFICER", "COMPETENT_AUTHORITY"] for r in self.roles):
            return True

        # Regional officer: must match region or broadcast role
        if "REGIONAL_OFFICER" in self.roles:
            if target_region and self.region and target_region == self.region:
                return True
            if target_role == "REGIONAL_OFFICER" and (not target_region or target_region == self.region):
                return True

        # Other officer roles (e.g. EVC Coordinator, Committee Member)
        if target_role and target_role in self.roles:
            return True

        return False


class NotificationSSEBroker:
    """
    In-memory asynchronous pub/sub broker for real-time Server-Sent Events.
    Maintains bounded client queues with automatic disconnect pruning.
    """

    def __init__(self):
        self.clients: Set[SSEClientConnection] = set()
        self._lock = asyncio.Lock()

    async def register_client(self, client: SSEClientConnection):
        async with self._lock:
            self.clients.add(client)
            logger.info(f"SSE client registered for user #{client.user_id} (active clients: {len(self.clients)})")

    async def unregister_client(self, client: SSEClientConnection):
        async with self._lock:
            client.is_active = False
            self.clients.discard(client)
            logger.info(f"SSE client removed for user #{client.user_id} (active clients: {len(self.clients)})")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcasts an authorized event summary to all eligible connected subscribers.
        Sanitizes payload: never broadcasts confidential document binaries or internal tokens.
        """
        sanitized_summary = {
            "event_type": event_type,
            "title": data.get("title") or data.get("subject") or "Regulatory Notification",
            "message": data.get("message") or data.get("body_text") or "",
            "level": data.get("level") or "INFO",
            "entity_type": data.get("entity_type"),
            "entity_id": data.get("entity_id"),
            "link_url": data.get("link_url"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "institution_id": data.get("institution_id"),
            "recipient_role": data.get("recipient_role")
        }

        async with self._lock:
            active_clients = list(self.clients)

        for client in active_clients:
            if client.is_active and client.is_authorized_for_event(data):
                try:
                    if client.queue.full():
                        # Drop oldest item to preserve bounded memory
                        try:
                            client.queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    await client.queue.put(sanitized_summary)
                except Exception as e:
                    logger.debug(f"Failed to queue SSE event for client #{client.user_id}: {e}")

    def get_active_clients_count(self) -> int:
        return len(self.clients)


_global_sse_broker = NotificationSSEBroker()


def get_sse_broker() -> NotificationSSEBroker:
    return _global_sse_broker

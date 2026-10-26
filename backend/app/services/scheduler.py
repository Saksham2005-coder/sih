import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alert import DeadlineEngineRun, SchedulerLease
from app.services.deadline_service import DeadlineService

logger = logging.getLogger("reguflow.scheduler")

class DeadlineScheduler:
    _instance: Optional["DeadlineScheduler"] = None
    _task: Optional[asyncio.Task] = None
    _is_running: bool = False
    _interval_seconds: int = 60
    _worker_id: str = str(uuid.uuid4())
    _lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "DeadlineScheduler":
        if cls._instance is None:
            cls._instance = DeadlineScheduler()
        return cls._instance

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    @property
    def worker_id(self) -> str:
        return self._worker_id

    async def start(self, interval_seconds: int = 60) -> None:
        async with self._lock:
            if self._is_running:
                logger.info("Deadline scheduler is already running.")
                return

            self._interval_seconds = interval_seconds
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info(f"Deadline scheduler started (worker={self._worker_id[:8]}) with {interval_seconds}s scan interval.")

    async def stop(self) -> None:
        async with self._lock:
            if not self._is_running:
                return

            self._is_running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None
            logger.info("Deadline scheduler stopped gracefully.")

    async def _run_loop(self) -> None:
        while self._is_running:
            try:
                # Run the scan in a background thread with an isolated database session
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._execute_scan)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error executing scheduled deadline scan: {e}", exc_info=True)

            try:
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                break

    @classmethod
    def acquire_lease(cls, db: Session, lease_name: str, holder_id: str, lease_duration_seconds: int = 60) -> bool:
        """Acquires a distributed database lease if free or expired."""
        now = datetime.now(timezone.utc)
        lease_duration = timedelta(seconds=lease_duration_seconds)
        lease = db.query(SchedulerLease).filter(SchedulerLease.lease_name == lease_name).first()

        if not lease:
            lease = SchedulerLease(
                lease_name=lease_name,
                holder_id=holder_id,
                acquired_at=now,
                expires_at=now + lease_duration,
                last_heartbeat=now
            )
            db.add(lease)
            db.commit()
            return True

        expires_at = lease.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now or lease.holder_id == holder_id:
            lease.holder_id = holder_id
            lease.acquired_at = now
            lease.expires_at = now + lease_duration
            lease.last_heartbeat = now
            db.commit()
            return True

        return False

    @classmethod
    def renew_lease(cls, db: Session, lease_name: str, holder_id: str, extension_seconds: int = 60) -> bool:
        """Renews an active lease if held by the caller."""
        now = datetime.now(timezone.utc)
        lease = db.query(SchedulerLease).filter(SchedulerLease.lease_name == lease_name).first()
        if not lease or lease.holder_id != holder_id:
            return False

        expires_at = lease.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            return False

        lease.expires_at = now + timedelta(seconds=extension_seconds)
        lease.last_heartbeat = now
        db.commit()
        return True

    @classmethod
    def release_lease(cls, db: Session, lease_name: str, holder_id: str) -> bool:
        """Releases a distributed lease held by the caller."""
        lease = db.query(SchedulerLease).filter(SchedulerLease.lease_name == lease_name).first()
        if lease and lease.holder_id == holder_id:
            db.delete(lease)
            db.commit()
            return True
        return False

    def _execute_scan(self) -> None:
        db = SessionLocal()
        try:
            # Check distributed database lease
            has_lease = self.acquire_lease(
                db,
                lease_name="deadline_engine_scan",
                holder_id=self._worker_id,
                lease_duration_seconds=max(120, self._interval_seconds * 2)
            )

            if not has_lease:
                logger.debug(f"Worker {self._worker_id[:8]} could not acquire scheduler lease. Skipping scan.")
                return

            DeadlineService.run_deadline_and_escalation_scan(db, trigger_mode="SCHEDULED")

            # Reliable Outbox: Asynchronously dispatch pending email/SMS notifications
            from app.services.notification.outbox_dispatcher import OutboxDispatcherService
            OutboxDispatcherService.dispatch_pending_outbox(db, batch_size=50)

        except Exception as e:
            logger.error(f"Error during scheduled execution or lease check: {e}")
        finally:
            db.close()

    def get_status(self, db: Session) -> Dict[str, Any]:
        last_run = db.query(DeadlineEngineRun).order_by(DeadlineEngineRun.created_at.desc()).first()
        runs = db.query(DeadlineEngineRun).all()
        
        return {
            "is_running": self._is_running,
            "scan_interval_seconds": self._interval_seconds,
            "last_run": last_run,
            "total_runs": len(runs),
            "total_scanned": sum(r.scanned_entities for r in runs),
            "total_reminders": sum(r.reminders_created for r in runs),
            "total_escalations": sum(r.escalations_created for r in runs),
            "total_duplicates_prevented": sum(r.duplicates_prevented for r in runs)
        }

scheduler = DeadlineScheduler.get_instance()

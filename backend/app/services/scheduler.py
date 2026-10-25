import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alert import DeadlineEngineRun
from app.services.deadline_service import DeadlineService

logger = logging.getLogger("reguflow.scheduler")

class DeadlineScheduler:
    _instance: Optional["DeadlineScheduler"] = None
    _task: Optional[asyncio.Task] = None
    _is_running: bool = False
    _interval_seconds: int = 60
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

    async def start(self, interval_seconds: int = 60) -> None:
        async with self._lock:
            if self._is_running:
                logger.info("Deadline scheduler is already running.")
                return

            self._interval_seconds = interval_seconds
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info(f"Deadline scheduler started with {interval_seconds}s scan interval.")

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

    def _execute_scan(self) -> None:
        db = SessionLocal()
        try:
            DeadlineService.run_deadline_and_escalation_scan(db, trigger_mode="SCHEDULED")
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

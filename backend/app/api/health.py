import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.config import settings
from app.services.scheduler import scheduler
from app.models.alert import DeadlineEngineRun, SchedulerLease

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive operational health and readiness endpoint."""
    t0 = time.perf_counter()
    db_status = "healthy"
    latency_ms = 0.0
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Inspect deadline scheduler and background telemetry
    now = datetime.now(timezone.utc)
    last_run = db.query(DeadlineEngineRun).order_by(DeadlineEngineRun.created_at.desc()).first()
    active_lease = db.query(SchedulerLease).filter(SchedulerLease.lease_name == "deadline_engine_scan").first()

    lease_info = None
    if active_lease:
        exp = active_lease.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        lease_info = {
            "holder_id": active_lease.holder_id,
            "acquired_at": active_lease.acquired_at.isoformat() if active_lease.acquired_at else None,
            "expires_at": exp.isoformat(),
            "is_active": exp > now
        }

    last_run_info = None
    is_telemetry_stale = False
    if last_run:
        run_dt = last_run.created_at
        if run_dt.tzinfo is None:
            run_dt = run_dt.replace(tzinfo=timezone.utc)
        last_run_info = {
            "run_id": last_run.run_id,
            "trigger_mode": last_run.trigger_mode,
            "status": last_run.status,
            "scanned_entities": last_run.scanned_entities,
            "reminders_created": last_run.reminders_created,
            "escalations_created": last_run.escalations_created,
            "duplicates_prevented": last_run.duplicates_prevented,
            "execution_time_ms": last_run.execution_time_ms,
            "executed_at": run_dt.isoformat()
        }
        # Telemetry is stale if last run was > 3x the scan interval ago
        staleness_threshold = timedelta(seconds=max(3600, scheduler.interval_seconds * 3))
        if (now - run_dt) > staleness_threshold:
            is_telemetry_stale = True

    overall_status = "online" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "service": "ReguFlow 360 Unified Regulatory Engine",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
        "database": db_status,
        "database_details": {
            "status": db_status,
            "latency_ms": latency_ms
        },
        "scheduler": {
            "configured": True,
            "is_running": scheduler.is_running,
            "worker_id": scheduler.worker_id,
            "scan_interval_seconds": scheduler.interval_seconds,
            "lease": lease_info,
            "last_run": last_run_info,
            "is_telemetry_stale": is_telemetry_stale
        },
        "timestamp_utc": now.isoformat(),
        "academic_cycle": "2026-2027"
    }

@router.get("/health/liveness")
def liveness_probe():
    """Simple lightweight liveness probe for container orchestrators."""
    return {"status": "alive", "timestamp_utc": datetime.now(timezone.utc).isoformat()}

@router.get("/health/readiness")
def readiness_probe(db: Session = Depends(get_db)):
    """Readiness probe that fails closed (503) if database is unavailable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: Database unreachable ({str(e)})"
        )

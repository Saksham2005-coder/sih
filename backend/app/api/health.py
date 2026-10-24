from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from app.core.database import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    return {
        "status": "online" if db_status == "healthy" else "degraded",
        "service": "ReguFlow 360 Unified Regulatory Engine",
        "version": "1.0.0",
        "database": db_status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "academic_cycle": "2026-2027",
    }

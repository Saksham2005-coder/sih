from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.seed.seed_data import seed_database

# Routers
from app.api import health, auth, applications, compliance, documents, evc, alerts, rules, audit, reports, document_intelligence, orders, notifications, demo

from app.services.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist (PostgreSQL and SQLite)
    Base.metadata.create_all(bind=engine)

    # Auto-hydrate database with full regulatory records if fresh (prevents empty database upon deployment)
    from app.core.database import SessionLocal
    from app.models.institution import Institution
    from app.models.application import Application
    from app.seed.restore_snapshot import load_snapshot

    db = SessionLocal()
    try:
        if db.query(Institution).count() == 0 or db.query(Application).count() == 0:
            print("AvedanSetu: Fresh database detected. Auto-hydrating records from snapshot...")
            load_snapshot(engine)
            print("AvedanSetu: Auto-hydration complete! All applications, users, and rules loaded.")
    except Exception as e:
        print(f"AvedanSetu startup database hydration check: {e}")
    finally:
        db.close()

    # Start autonomous background deadline engine
    await scheduler.start(interval_seconds=60)
    yield
    # Graceful shutdown
    await scheduler.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Integrated AICTE Approval Workflow Automation, Compliance Monitoring, and Alert Management System (SIH 2026 PS 26262)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api and root health
app.include_router(health.router)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(compliance.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(evc.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(rules.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(document_intelligence.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "classification": "Prototype for SIH 2026 AICTE PS 26262",
        "api_docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

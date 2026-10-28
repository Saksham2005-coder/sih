import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Engine setup
raw_url = settings.DATABASE_URL
# Render, Supabase, Neon, and Railway often provision DATABASE_URL with 'postgres://'
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)
elif raw_url.startswith("sqlite:///./"):
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rel_part = raw_url[len("sqlite:///./"):]
    db_file = os.path.join(backend_dir, rel_part)
    raw_url = f"sqlite:///{db_file.replace(os.sep, '/')}"

connect_args = {}
if raw_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    raw_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

# Enable SQLite foreign key enforcement
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

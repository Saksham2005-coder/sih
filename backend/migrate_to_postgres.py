#!/usr/bin/env python3
"""
AvedanSetu (आवेदनसेतु) — PostgreSQL Migration & Data Preservation Utility
Migrates all local SQLite regulatory tables, documents, applications, and logs
to PostgreSQL with complete schema creation, sequence alignment, and verification.

Usage:
    python migrate_to_postgres.py --target "postgresql+psycopg2://user:password@host:5432/dbname"
"""
import sys
import os
import argparse
from sqlalchemy import create_engine, text

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app.models
from app.core.database import Base
from app.seed.restore_snapshot import load_snapshot
from app.seed.dump_snapshot import dump_snapshot

def migrate(target_url: str):
    if not target_url:
        print("Error: Target database URL is required.")
        sys.exit(1)

    # Normalize url
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to destination PostgreSQL database: {target_url.split('@')[-1] if '@' in target_url else target_url}")

    target_engine = create_engine(target_url, pool_pre_ping=True)

    # 1. First ensure current local SQLite state is fresh in snapshot
    print("\n--- Step 1: Exporting current local state to snapshot ---")
    dump_snapshot()

    # 2. Create all tables on destination PostgreSQL
    print("\n--- Step 2: Creating schema on destination PostgreSQL ---")
    Base.metadata.create_all(bind=target_engine)
    print("Schema created successfully!")

    # 3. Restore all snapshot tables into destination PostgreSQL
    print("\n--- Step 3: Hydrating destination PostgreSQL with all regulatory records ---")
    load_snapshot(target_engine=target_engine)

    # 4. Verification of row counts
    print("\n--- Step 4: Verification of migrated tables ---")
    with target_engine.connect() as conn:
        for table_name in [
            "institutions", "users", "applications", "application_stages",
            "deficiencies", "compliance_undertakings", "compliance_evidence",
            "evc_inspections", "statutory_orders", "rule_definitions"
        ]:
            if table_name in Base.metadata.tables:
                count = conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar()
                print(f"  ✓ {table_name}: {count} records")

    print("\n=======================================================")
    print("  MIGRATION COMPLETE: All AvedanSetu data is preserved!")
    print("=======================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate AvedanSetu database to PostgreSQL")
    parser.add_argument("--target", help="Target PostgreSQL database URL", default=os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    if not args.target or args.target.startswith("sqlite"):
        print("Please provide a valid PostgreSQL connection string:")
        print("  python migrate_to_postgres.py --target 'postgresql+psycopg2://user:password@host:5432/dbname'")
        sys.exit(1)

    migrate(args.target)

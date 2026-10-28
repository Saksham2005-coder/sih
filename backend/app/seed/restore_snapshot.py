import json
import os
from datetime import datetime, date
from sqlalchemy import create_engine, text
import app.models  # Register all models with Base.metadata
from app.core.database import Base, engine, SessionLocal
from app.core.config import settings

def load_snapshot(target_engine=None):
    if target_engine is None:
        target_engine = engine

    # Ensure tables exist on target database
    Base.metadata.create_all(bind=target_engine)

    json_path = os.path.join(os.path.dirname(__file__), "snapshot_data.json")
    if not os.path.exists(json_path):
        print(f"Snapshot file not found at {json_path}")
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        dump = json.load(f)

    with target_engine.begin() as conn:
        for table_name, rows in dump.items():
            if table_name not in Base.metadata.tables:
                print(f"Skipping table {table_name} (not in models)")
                continue

            table = Base.metadata.tables[table_name]

            # Check if table already has rows
            existing_count = conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar()
            if existing_count > 0:
                print(f"Table {table_name} already has {existing_count} rows, skipping insert.")
                continue

            if not rows:
                continue

            cleaned_rows = []
            for row in rows:
                cleaned = {}
                for col_name, val in row.items():
                    if col_name not in table.columns:
                        continue
                    col = table.columns[col_name]
                    if val is not None:
                        type_str = str(col.type).lower()
                        if "datetime" in type_str and isinstance(val, str):
                            try:
                                val = datetime.fromisoformat(val.replace("Z", "+00:00"))
                            except Exception:
                                pass
                        elif "date" in type_str and isinstance(val, str) and not "datetime" in type_str:
                            try:
                                val = date.fromisoformat(val)
                            except Exception:
                                pass
                        elif "bool" in type_str and isinstance(val, (int, str)):
                            val = bool(val)
                        elif "json" in type_str and isinstance(val, str):
                            try:
                                val = json.loads(val)
                            except Exception:
                                pass
                    cleaned[col_name] = val
                cleaned_rows.append(cleaned)

            if cleaned_rows:
                conn.execute(table.insert(), cleaned_rows)
                print(f"Restored {len(cleaned_rows)} rows into {table_name}")

        # In PostgreSQL, reset primary key sequence values to prevent duplicate key violations on subsequent inserts
        if target_engine.dialect.name == "postgresql":
            for table_name in dump.keys():
                if table_name in Base.metadata.tables:
                    try:
                        conn.execute(text(f"""
                            SELECT setval(
                                pg_get_serial_sequence('"{table_name}"', 'id'),
                                coalesce(max(id), 1)
                            ) FROM "{table_name}";
                        """))
                    except Exception:
                        pass

    print("Snapshot restoration complete!")
    return True

if __name__ == "__main__":
    load_snapshot()

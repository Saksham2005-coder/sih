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

    results = {}
    for table_name, rows in dump.items():
        if table_name not in Base.metadata.tables:
            print(f"Skipping table {table_name} (not in models)")
            continue

        table = Base.metadata.tables[table_name]

        # Use individual transaction per table to avoid rolling back everything if one table has an issue
        try:
            with target_engine.begin() as conn:
                existing_count = conn.execute(text(f'SELECT count(*) FROM "{table_name}"')).scalar()
                if existing_count > 0:
                    print(f"Table {table_name} already has {existing_count} rows, skipping insert.")
                    results[table_name] = existing_count
                    continue

                if not rows:
                    results[table_name] = 0
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
                    results[table_name] = len(cleaned_rows)
        except Exception as exc:
            print(f"Error restoring table {table_name}: {exc}")
            results[table_name] = f"error: {str(exc)}"

    # In PostgreSQL, safely reset primary key sequence values
    if target_engine.dialect.name == "postgresql":
        for table_name in dump.keys():
            if table_name in Base.metadata.tables and "id" in Base.metadata.tables[table_name].columns:
                try:
                    with target_engine.begin() as conn:
                        seq = conn.execute(text(f"SELECT pg_get_serial_sequence('{table_name}', 'id')")).scalar()
                        if seq:
                            conn.execute(text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM \"{table_name}\"), 1))"))
                except Exception as seq_err:
                    print(f"Sequence reset note for {table_name}: {seq_err}")

    print("Snapshot restoration complete!")
    return results

if __name__ == "__main__":
    load_snapshot()

import json
import os
from datetime import datetime, date
from sqlalchemy import text
import app.models
from app.core.database import Base, engine

def dump_snapshot(source_engine=None, output_path=None):
    if source_engine is None:
        source_engine = engine

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "snapshot_data.json")

    # Topological table insertion order
    ordered_tables = [
        "institutions",
        "users",
        "user_roles",
        "applications",
        "application_stages",
        "deficiencies",
        "compliance_undertakings",
        "compliance_evidence",
        "document_records",
        "document_versions",
        "document_analyses",
        "evc_inspections",
        "evc_experts",
        "evc_panel_assignments",
        "evc_field_evidence",
        "statutory_orders",
        "notifications",
        "notification_outbox",
        "alert_escalations",
        "rule_definitions",
        "rule_version_history",
        "audit_events",
        "deadline_engine_runs",
        "scheduler_leases",
        "revoked_tokens",
    ]

    dump = {}
    with source_engine.connect() as conn:
        for table_name in ordered_tables:
            if table_name not in Base.metadata.tables:
                continue

            table = Base.metadata.tables[table_name]
            result = conn.execute(table.select()).mappings().all()
            rows = []
            for row in result:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, (datetime, date)):
                        d[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        d[k] = v.decode("utf-8", errors="ignore")
                rows.append(d)
            dump[table_name] = rows
            print(f"Dumped {len(rows)} rows from {table_name}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2, ensure_ascii=False)

    print(f"Database snapshot dumped successfully to {output_path}")
    return True

if __name__ == "__main__":
    dump_snapshot()

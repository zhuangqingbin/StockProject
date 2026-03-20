from __future__ import annotations

from apps.data_hub.data_explorer.backend.infrastructure.db import get_engine
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    get_table_columns,
    get_table_constraints,
    get_table_ddl,
    get_table_indexes,
)
from apps.data_hub.data_explorer.backend.services.catalog_service import (
    get_table_database_source,
    get_table_registry,
    get_table_stats,
)
from apps.data_hub.data_explorer.backend.services.monitor_service import list_table_recent_runs


def get_table_summary(table_name: str) -> dict[str, object]:
    return get_table_stats([table_name]).get(
        table_name,
        {
            "row_count": 0,
            "earliest_data_date": None,
            "latest_data_date": None,
            "last_updated": None,
            "status": "error",
        },
    )


def get_table_structure(table_name: str) -> dict[str, object]:
    registry = get_table_registry()
    engine = get_engine(get_table_database_source(table_name, registry))
    field_labels = registry.get(table_name, {}).get("field_labels", {})
    try:
        columns = []
        for column in get_table_columns(engine, table_name):
            normalized = dict(column)
            label = field_labels.get(str(column.get("name"))) if isinstance(field_labels, dict) else None
            if label:
                normalized["label"] = label
            columns.append(normalized)

        return {
            "columns": columns,
            "indexes": get_table_indexes(engine, table_name),
            "constraints": get_table_constraints(engine, table_name),
            "ddl": get_table_ddl(engine, table_name),
        }
    except Exception:
        return {
            "columns": [],
            "indexes": [],
            "constraints": [],
            "ddl": "",
        }


def get_table_detail(table_name: str) -> dict[str, object]:
    registry = get_table_registry()
    if table_name not in registry:
        raise KeyError(table_name)

    entry = registry[table_name]
    return {
        "table_name": table_name,
        "category": entry["category"],
        "description": entry["description"],
        "api_name": entry.get("api_name", ""),
        "api_url": entry.get("api_url", ""),
        "job_name": entry["job_name"],
        "job_description": entry.get("job_description", ""),
        "trigger_profile": entry["trigger_profile"],
        "summary": get_table_summary(table_name),
        "structure": get_table_structure(table_name),
        "recent_runs": list_table_recent_runs(table_name),
    }

from __future__ import annotations

from collections import Counter

from apps.data_hub.data_explorer.backend.infrastructure.db import get_engine
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    get_current_schema_name,
)
from apps.data_hub.data_explorer.backend.services.catalog_service import get_table_registry
from apps.data_hub.data_explorer.backend.services.table_detail_service import get_table_detail


def _load_schema_name(source: str) -> str | None:
    try:
        return get_current_schema_name(get_engine(source))
    except Exception:
        return None


def get_schema_overview() -> dict[str, object]:
    registry = get_table_registry()
    category_counts = Counter(entry["category"] for entry in registry.values())
    schema_names = {
        "ts": _load_schema_name("ts"),
        "ak": _load_schema_name("ak"),
    }

    return {
        "schema_name": schema_names["ts"],
        "schema_names": schema_names,
        "table_count": len(registry),
        "category_counts": dict(category_counts),
        "runtime_table_count": category_counts.get("runtime", 0),
    }


def get_table_metadata_detail(table_name: str) -> dict[str, object]:
    detail = get_table_detail(table_name)
    structure = detail["structure"]
    return {
        "columns": structure.get("columns", []),
        "indexes": structure.get("indexes", []),
        "constraints": structure.get("constraints", []),
        "ddl": structure.get("ddl", ""),
    }

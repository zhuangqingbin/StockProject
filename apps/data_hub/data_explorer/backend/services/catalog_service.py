from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from functools import lru_cache
import inspect
from pathlib import Path
import re
from typing import TYPE_CHECKING, Literal, cast

from apps.data_hub.data_explorer.backend.infrastructure.db import get_engine
from apps.data_hub.data_explorer.backend.infrastructure.catalog_loader import load_table_catalog
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    get_approximate_row_count,
    get_earliest_data_date,
    get_exact_row_count,
    get_latest_data_date,
    get_latest_job_success_time,
    get_table_columns,
)
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS
from apps.data_hub.data_pipeline_ts.jobs.catalog import INFRASTRUCTURE_TARGETS
from apps.data_hub.data_explorer.backend.services.time_utils import format_shanghai_timestamp

if TYPE_CHECKING:
    from apps.data_hub.data_explorer.backend.infrastructure.db import DatabaseSource


FETCHER_ROOT = (
    Path(__file__).resolve().parents[3] / "data_pipeline_ts" / "fetchers"
)
API_URL_RE = re.compile(r"API:\s*(https?://\S+)")
FIELD_LINE_RE = re.compile(r"^[\"'](?P<name>[^\"']+)[\"']\s*,?\s*(?:#\s*(?P<label>.+))?$")
STATUS_PRIORITY = {
    "delayed": 0,
    "no_data": 1,
    "error": 2,
    "normal": 3,
    "manual": 4,
}
VALID_DATABASE_SOURCES = {"ts", "ak"}
DEFAULT_DATABASE_SOURCE = "ts"
RowCountMode = Literal["exact", "approximate"]


def _derive_status(
    *,
    row_count: int,
    latest_data_date: str | None,
    last_updated: str | None,
    has_job_binding: bool,
) -> str:
    if row_count == 0:
        return "no_data"
    if latest_data_date and _is_stale(latest_data_date):
        return "delayed"
    if has_job_binding and last_updated is None:
        return "error"
    return "manual" if not has_job_binding else "normal"


def _is_stale(value: str) -> bool:
    candidates = ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S")
    for pattern in candidates:
        try:
            parsed = datetime.strptime(value[: len(pattern.replace("%", ""))], pattern).date()
            return (date.today() - parsed).days > 3
        except ValueError:
            continue
    return False


def _discover_fetcher_tables() -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {}
    for path in FETCHER_ROOT.rglob("*.py"):
        if path.name == "__init__.py" or path.parent == FETCHER_ROOT:
            continue
        categories.setdefault(path.parent.name, []).append(path.stem)
    return {key: sorted(value) for key, value in categories.items()}


def _load_job_metadata() -> dict[str, dict[str, str]]:
    return {
        job.table_name: {
            "job_name": job.name,
            "job_description": job.description,
            "trigger_profile": job.profile.value,
            "api_name": job.api_name,
        }
        for job in ALL_JOBS
    }


def _load_fetcher_bindings() -> dict[str, type[Any]]:
    bindings = {
        job.table_name: job.fetcher_cls
        for job in ALL_JOBS
    }
    bindings.update(
        {
            target.table_name: target.fetcher_cls
            for target in INFRASTRUCTURE_TARGETS.values()
        }
    )
    return bindings


def _build_registry_entry(
    *,
    table_name: str,
    category: str,
    description: str,
    job_metadata: dict[str, dict[str, str]],
    fetcher_cls: type[Any] | None,
) -> dict[str, object]:
    metadata = job_metadata.get(table_name, {})
    return {
        "table_name": table_name,
        "category": category,
        "description": description,
        "job_name": metadata.get("job_name", ""),
        "job_description": metadata.get("job_description", ""),
        "trigger_profile": metadata.get("trigger_profile", ""),
        "api_name": metadata.get("api_name", ""),
        "api_url": _extract_api_url(fetcher_cls),
        "field_labels": _extract_field_labels(fetcher_cls),
        "database_source": DEFAULT_DATABASE_SOURCE,
    }


def _coerce_database_source(source: object, *, table_name: str) -> "DatabaseSource":
    normalized = str(source or DEFAULT_DATABASE_SOURCE)
    if normalized not in VALID_DATABASE_SOURCES:
        raise ValueError(
            f"unknown database source for table '{table_name}': {normalized}"
        )
    return cast("DatabaseSource", normalized)


def _validate_discovered_fetcher_contract(
    *,
    table_name: str,
    discovered_category: str,
    catalog_category: str | None,
    fetcher_cls: type[Any] | None,
) -> None:
    if fetcher_cls is None:
        raise ValueError(
            f"missing fetcher binding for discovered fetcher table '{table_name}'"
        )

    if catalog_category is None or catalog_category == discovered_category:
        return

    raise ValueError(
        "category drift for discovered fetcher table "
        f"'{table_name}': discovered '{discovered_category}', "
        f"catalog '{catalog_category}'"
    )


def _validate_registry_categories(
    *,
    catalog_categories: set[str],
    registry: dict[str, dict[str, object]],
) -> None:
    unknown_categories = sorted(
        {
            str(entry.get("category", ""))
            for entry in registry.values()
            if str(entry.get("category", "")) not in catalog_categories
        }
    )
    if not unknown_categories:
        return

    raise ValueError(
        "unknown category present in table registry: " + ", ".join(unknown_categories)
    )


def _extract_api_url(fetcher_cls: type[Any] | None) -> str:
    if fetcher_cls is None:
        return ""

    docstring = inspect.getdoc(fetcher_cls) or ""
    match = API_URL_RE.search(docstring)
    return match.group(1) if match else ""


def _extract_field_labels(fetcher_cls: type[Any] | None) -> dict[str, str]:
    if fetcher_cls is None:
        return {}

    labels: dict[str, str] = {}
    table_schema = getattr(fetcher_cls, "table_schema", None)
    schema_columns = getattr(table_schema, "columns", {})
    for field_name, column in schema_columns.items():
        comment = str(getattr(column, "comment", "") or "").strip()
        if comment:
            labels[str(field_name)] = comment

    try:
        source = inspect.getsource(fetcher_cls)
    except (OSError, TypeError):
        source = ""

    in_fields_block = False
    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not in_fields_block:
            if stripped.startswith("fields") and "[" in stripped:
                in_fields_block = True
            continue

        if stripped.startswith("]"):
            break

        match = FIELD_LINE_RE.match(stripped)
        if not match:
            continue

        label = str(match.group("label") or "").strip()
        if label:
            labels[match.group("name")] = label

    return labels


@lru_cache(maxsize=1)
def get_table_registry() -> dict[str, dict[str, object]]:
    catalog = load_table_catalog()
    job_metadata = _load_job_metadata()
    fetcher_bindings = _load_fetcher_bindings()
    registry: dict[str, dict[str, str]] = {}

    for category, table_names in _discover_fetcher_tables().items():
        if category not in catalog.categories:
            continue
        for table_name in table_names:
            if table_name in catalog.excluded_tables:
                continue
            config_entry = catalog.tables.get(table_name)
            fetcher_cls = fetcher_bindings.get(table_name)
            _validate_discovered_fetcher_contract(
                table_name=table_name,
                discovered_category=category,
                catalog_category=config_entry.category if config_entry else None,
                fetcher_cls=fetcher_cls,
            )
            registry[table_name] = _build_registry_entry(
                table_name=table_name,
                category=category,
                description=config_entry.description if config_entry else table_name,
                job_metadata=job_metadata,
                fetcher_cls=fetcher_cls,
            )

    for table_name, config_entry in catalog.tables.items():
        if table_name in catalog.excluded_tables or table_name in registry:
            continue
        fetcher_cls = fetcher_bindings.get(table_name)
        registry[table_name] = _build_registry_entry(
            table_name=table_name,
            category=config_entry.category,
            description=config_entry.description,
            job_metadata=job_metadata,
            fetcher_cls=fetcher_cls,
        )

    return registry


def get_table_database_source(
    table_name: str,
    registry: dict[str, dict[str, object]] | None = None,
) -> "DatabaseSource":
    active_registry = registry or get_table_registry()
    entry = active_registry.get(table_name, {})
    return _coerce_database_source(entry.get("database_source"), table_name=table_name)


def get_table_stats(
    table_names: list[str],
    *,
    row_count_mode: RowCountMode = "exact",
) -> dict[str, dict[str, object]]:
    registry = get_table_registry()
    stats: dict[str, dict[str, object]] = {}
    row_count_reader = (
        get_exact_row_count
        if row_count_mode == "exact"
        else get_approximate_row_count
    )

    for table_name in table_names:
        engine = get_engine(get_table_database_source(table_name, registry))
        job_name = str(registry.get(table_name, {}).get("job_name", ""))
        try:
            columns = get_table_columns(engine, table_name)
            row_count = row_count_reader(engine, table_name)
            earliest_data_date = get_earliest_data_date(engine, table_name, columns)
            latest_data_date = get_latest_data_date(engine, table_name, columns)
            last_updated = (
                format_shanghai_timestamp(get_latest_job_success_time(engine, job_name))
                if job_name
                else None
            )
            status = _derive_status(
                row_count=row_count,
                latest_data_date=latest_data_date,
                last_updated=last_updated,
                has_job_binding=bool(job_name),
            )
        except Exception:
            row_count = 0
            earliest_data_date = None
            latest_data_date = None
            last_updated = None
            status = "error"

        stats[table_name] = {
            "row_count": row_count,
            "earliest_data_date": earliest_data_date,
            "latest_data_date": latest_data_date,
            "last_updated": last_updated,
            "status": status,
        }

    return stats


def list_categories() -> list[dict[str, object]]:
    catalog = load_table_catalog()
    registry = get_table_registry()
    _validate_registry_categories(
        catalog_categories=set(catalog.categories),
        registry=registry,
    )
    counts = Counter(item["category"] for item in registry.values())
    return [
        {
            "key": key,
            "label": value.label,
            "table_count": counts.get(key, 0),
        }
        for key, value in catalog.categories.items()
        if key != "database_metadata"
    ]


def list_tables_by_category(category_key: str) -> list[dict[str, object]]:
    tables = [
        value
        for value in get_table_registry().values()
        if value["category"] == category_key
    ]
    stats = get_table_stats(
        [item["table_name"] for item in tables],
        row_count_mode="approximate",
    )

    rows = [
        {
            **item,
            **stats.get(item["table_name"], {}),
        }
        for item in tables
    ]
    rows.sort(key=lambda item: str(item.get("last_updated") or ""), reverse=True)
    rows.sort(key=lambda item: STATUS_PRIORITY.get(str(item.get("status", "normal")), 99))
    return rows

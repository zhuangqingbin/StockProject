from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CategoryCatalog:
    key: str
    label: str


@dataclass(frozen=True)
class TableCatalogEntry:
    table_name: str
    category: str
    description: str


@dataclass(frozen=True)
class TableCatalog:
    categories: dict[str, CategoryCatalog]
    tables: dict[str, TableCatalogEntry]
    excluded_tables: frozenset[str]


def get_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "table_catalog.yaml"


def _load_raw_catalog(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _validate_table_categories(
    *,
    categories: dict[str, CategoryCatalog],
    tables: dict[str, TableCatalogEntry],
) -> None:
    unknown_categories = sorted(
        {
            entry.category
            for entry in tables.values()
            if entry.category not in categories
        }
    )
    if not unknown_categories:
        return

    raise ValueError(
        "unknown category referenced in table catalog: "
        + ", ".join(unknown_categories)
    )


@lru_cache(maxsize=1)
def load_table_catalog(path: str | None = None) -> TableCatalog:
    catalog_path = Path(path) if path else get_catalog_path()
    raw_catalog = _load_raw_catalog(catalog_path)

    raw_categories = raw_catalog.get("categories", {})
    raw_tables = raw_catalog.get("tables", {})
    raw_excluded_tables = raw_catalog.get("excluded_tables", [])

    categories = {
        key: CategoryCatalog(key=key, label=str(value["label"]))
        for key, value in raw_categories.items()
    }
    tables = {
        table_name: TableCatalogEntry(
            table_name=table_name,
            category=str(value["category"]),
            description=str(value["description"]),
        )
        for table_name, value in raw_tables.items()
    }
    _validate_table_categories(categories=categories, tables=tables)

    return TableCatalog(
        categories=categories,
        tables=tables,
        excluded_tables=frozenset(str(item) for item in raw_excluded_tables),
    )

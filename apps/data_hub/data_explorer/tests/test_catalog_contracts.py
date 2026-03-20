from __future__ import annotations

import pytest

from apps.data_hub.data_explorer.backend.infrastructure.catalog_loader import (
    CategoryCatalog,
    TableCatalog,
    TableCatalogEntry,
)
from apps.data_hub.data_explorer.backend.services import catalog_service


class DummyFetch:
    fields = ["trade_date"]


def _make_catalog(*, category: str) -> TableCatalog:
    return TableCatalog(
        categories={
            "stock_market_data": CategoryCatalog(
                key="stock_market_data",
                label="Stock Market Data",
            ),
            "board_data": CategoryCatalog(
                key="board_data",
                label="Board Data",
            ),
        },
        tables={
            "stock_daily": TableCatalogEntry(
                table_name="stock_daily",
                category=category,
                description="A股日线行情",
            )
        },
        excluded_tables=frozenset(),
    )


def test_get_table_registry_rejects_category_drift_between_fetchers_and_catalog(monkeypatch):
    catalog_service.get_table_registry.cache_clear()
    monkeypatch.setattr(
        catalog_service,
        "load_table_catalog",
        lambda: _make_catalog(category="board_data"),
    )
    monkeypatch.setattr(
        catalog_service,
        "_discover_fetcher_tables",
        lambda: {"stock_market_data": ["stock_daily"]},
    )
    monkeypatch.setattr(
        catalog_service,
        "_load_fetcher_bindings",
        lambda: {"stock_daily": DummyFetch},
    )
    monkeypatch.setattr(
        catalog_service,
        "_load_job_metadata",
        lambda: {
            "stock_daily": {
                "job_name": "stock_daily",
                "job_description": "股票日线行情",
                "trigger_profile": "trade_day_post_close_core",
                "api_name": "daily",
            }
        },
    )

    with pytest.raises(ValueError, match="category drift"):
        catalog_service.get_table_registry()

    catalog_service.get_table_registry.cache_clear()


def test_get_table_registry_rejects_discovered_fetcher_without_binding(monkeypatch):
    catalog_service.get_table_registry.cache_clear()
    monkeypatch.setattr(
        catalog_service,
        "load_table_catalog",
        lambda: _make_catalog(category="stock_market_data"),
    )
    monkeypatch.setattr(
        catalog_service,
        "_discover_fetcher_tables",
        lambda: {"stock_market_data": ["stock_daily"]},
    )
    monkeypatch.setattr(catalog_service, "_load_fetcher_bindings", lambda: {})
    monkeypatch.setattr(catalog_service, "_load_job_metadata", lambda: {})

    with pytest.raises(ValueError, match="missing fetcher binding"):
        catalog_service.get_table_registry()

    catalog_service.get_table_registry.cache_clear()


def test_get_table_registry_ignores_discovered_fetchers_outside_catalog_categories(monkeypatch):
    catalog_service.get_table_registry.cache_clear()
    monkeypatch.setattr(
        catalog_service,
        "load_table_catalog",
        lambda: _make_catalog(category="stock_market_data"),
    )
    monkeypatch.setattr(
        catalog_service,
        "_discover_fetcher_tables",
        lambda: {
            "stock_market_data": ["stock_daily"],
            "special_data": ["stock_ccass_hold"],
        },
    )
    monkeypatch.setattr(
        catalog_service,
        "_load_fetcher_bindings",
        lambda: {"stock_daily": DummyFetch},
    )
    monkeypatch.setattr(
        catalog_service,
        "_load_job_metadata",
        lambda: {
            "stock_daily": {
                "job_name": "stock_daily",
                "job_description": "股票日线行情",
                "trigger_profile": "trade_day_post_close_core",
                "api_name": "daily",
            }
        },
    )

    registry = catalog_service.get_table_registry()

    assert "stock_daily" in registry
    assert "stock_ccass_hold" not in registry

    catalog_service.get_table_registry.cache_clear()


def test_get_table_registry_current_contract_exposes_job_and_infrastructure_entries():
    catalog_service.get_table_registry.cache_clear()
    registry = catalog_service.get_table_registry()

    assert registry["stock_daily"]["job_name"] == "stock_daily"
    assert registry["stock_daily"]["trigger_profile"] == "trade_day_post_close_core"
    assert registry["trade_cal"]["category"] == "basic_data"
    assert registry["trade_cal"]["job_name"] == ""


def test_get_table_registry_current_contract_hides_removed_index_daily_and_exposes_special_data():
    catalog_service.get_table_registry.cache_clear()
    registry = catalog_service.get_table_registry()
    categories = {item["key"] for item in catalog_service.list_categories()}

    assert "stock_index_daily" not in registry
    assert "special_data" in categories
    assert registry["stock_ccass_hold"]["category"] == "special_data"
    assert registry["stock_stk_ah_comparison"]["category"] == "special_data"

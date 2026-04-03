import pytest

from apps.data_hub.data_explorer.backend.infrastructure.catalog_loader import load_table_catalog
from apps.data_hub.data_explorer.backend.services.catalog_service import (
    get_table_stats,
    list_categories,
    list_tables_by_category,
)
from apps.data_hub.data_explorer.backend.services.table_detail_service import (
    get_table_detail,
    get_table_structure,
    get_table_summary,
)


def test_list_categories_includes_counts():
    categories = list_categories()
    categories_by_key = {item["key"]: item for item in categories}

    assert categories_by_key["basic_data"]["table_count"] == 6
    assert categories_by_key["stock_market_data"]["table_count"] == 7
    assert categories_by_key["special_data"]["table_count"] == 8
    assert categories_by_key["runtime"]["table_count"] == 1


def test_list_categories_rejects_registry_entries_with_unknown_category(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.load_table_catalog",
        lambda: load_table_catalog(),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_registry",
        lambda: {
            "stock_daily": {"category": "stock_market_data"},
            "rogue_table": {"category": "ghost_data"},
        },
    )

    with pytest.raises(ValueError, match="unknown category"):
        list_categories()


def test_list_tables_by_category_returns_only_current_category(monkeypatch):
    def fake_stats(
        table_names: list[str],
        *,
        row_count_mode: str = "exact",
    ) -> dict[str, dict[str, object]]:
        assert row_count_mode == "approximate"
        return {
            "stock_daily": {
                "row_count": 5230000,
                "earliest_data_date": "19901219",
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T18:05:00",
                "status": "normal",
            },
            "stock_daily_basic": {
                "row_count": 5230000,
                "earliest_data_date": "19901219",
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T18:06:00",
                "status": "normal",
            },
        }

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_stats",
        fake_stats,
    )

    tables = list_tables_by_category("stock_market_data")
    tables_by_name = {item["table_name"]: item for item in tables}

    assert [item["table_name"] for item in tables][:2] == ["stock_daily_basic", "stock_daily"]
    assert all(item["category"] == "stock_market_data" for item in tables)
    assert tables_by_name["stock_daily"]["api_name"] == "daily"
    assert tables_by_name["stock_daily"]["job_description"] == "股票日线行情"
    assert tables_by_name["stock_daily"]["api_url"] == "https://tushare.pro/document/2?doc_id=27"


def test_list_tables_by_category_uses_approximate_row_counts(monkeypatch):
    captured: dict[str, object] = {}

    def fake_stats(
        table_names: list[str],
        *,
        row_count_mode: str,
    ) -> dict[str, dict[str, object]]:
        captured["row_count_mode"] = row_count_mode
        return {
            table_name: {
                "row_count": 1,
                "earliest_data_date": "19901219",
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T18:05:00",
                "status": "normal",
            }
            for table_name in table_names
        }

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_stats",
        fake_stats,
    )

    list_tables_by_category("stock_market_data")

    assert captured["row_count_mode"] == "approximate"


def test_get_table_detail_aggregates_structure_and_summary(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_summary",
        lambda table_name: {
            "row_count": 5230000,
            "earliest_data_date": "19901219",
            "latest_data_date": "20260317",
            "last_updated": "2026-03-17T18:05:00",
            "status": "normal",
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_structure",
        lambda table_name: {
            "columns": [{"name": "trade_date", "type": "CHAR(8)"}],
            "indexes": [{"name": "PRIMARY", "columns": ["id"], "primary": True, "unique": True}],
            "constraints": [{"name": "pk_stock_daily", "type": "PRIMARY KEY"}],
            "ddl": "CREATE TABLE `stock_daily` (...)",
        },
    )

    detail = get_table_detail("stock_daily")

    assert detail["table_name"] == "stock_daily"
    assert detail["category"] == "stock_market_data"
    assert detail["description"] == "A股日线行情"
    assert detail["api_name"] == "daily"
    assert detail["job_description"] == "股票日线行情"
    assert detail["api_url"] == "https://tushare.pro/document/2?doc_id=27"
    assert detail["summary"]["row_count"] == 5230000
    assert detail["structure"]["columns"][0]["name"] == "trade_date"
    assert detail["structure"]["ddl"] == "CREATE TABLE `stock_daily` (...)"


def test_get_table_stats_reads_exact_counts_date_range_and_last_successful_update(monkeypatch):
    sentinel_ts_engine = object()
    sentinel_ak_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_engine",
        lambda source: {
            "ts": sentinel_ts_engine,
            "ak": sentinel_ak_engine,
        }[source],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_columns",
        lambda engine, table_name: (
            [{"name": "trade_date"}, {"name": "ts_code"}]
            if engine is sentinel_ts_engine
            else [{"name": "cal_date"}]
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_exact_row_count",
        lambda engine, table_name: (
            5230000 if table_name == "stock_daily" else 365
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_latest_data_date",
        lambda engine, table_name, columns: (
            "20260317" if table_name == "stock_daily" else "20260318"
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_earliest_data_date",
        lambda engine, table_name, columns: (
            "19901219" if table_name == "stock_daily" else "20250318"
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_latest_job_success_time",
        lambda engine, job_name: (
            "2026-03-17T18:05:00"
            if engine is sentinel_ts_engine and job_name == "stock_daily"
            else None
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_registry",
        lambda: {
            "stock_daily": {"job_name": "stock_daily", "database_source": "ts"},
            "ak_trade_cal": {"job_name": "", "database_source": "ak"},
        },
    )

    stats = get_table_stats(["stock_daily", "ak_trade_cal"])

    assert stats["stock_daily"] == {
        "row_count": 5230000,
        "earliest_data_date": "19901219",
        "latest_data_date": "20260317",
        "last_updated": "2026-03-17T18:05:00",
        "status": "normal",
    }
    assert stats["ak_trade_cal"] == {
        "row_count": 365,
        "earliest_data_date": "20250318",
        "latest_data_date": "20260318",
        "last_updated": None,
        "status": "manual",
    }


def test_get_table_stats_can_use_approximate_row_counts(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_engine",
        lambda source: sentinel_engine,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_columns",
        lambda engine, table_name: [{"name": "trade_date"}, {"name": "ts_code"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_exact_row_count",
        lambda engine, table_name: (_ for _ in ()).throw(AssertionError("exact count should not be used")),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_approximate_row_count",
        lambda engine, table_name: 5200000,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_latest_data_date",
        lambda engine, table_name, columns: "20260317",
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_earliest_data_date",
        lambda engine, table_name, columns: "19901219",
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_latest_job_success_time",
        lambda engine, job_name: "2026-03-17T18:05:00",
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.catalog_service.get_table_registry",
        lambda: {
            "stock_daily": {"job_name": "stock_daily", "database_source": "ts"},
        },
    )

    stats = get_table_stats(["stock_daily"], row_count_mode="approximate")

    assert stats["stock_daily"] == {
        "row_count": 5200000,
        "earliest_data_date": "19901219",
        "latest_data_date": "20260317",
        "last_updated": "2026-03-17T18:05:00",
        "status": "normal",
    }


def test_table_detail_helpers_use_runtime_introspection(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_engine",
        lambda source: sentinel_engine if source == "ak" else object(),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "field_labels": {"trade_date": "交易日期"},
                "database_source": "ak",
            }
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_stats",
        lambda table_names: {
            "stock_daily": {
                "row_count": 5230000,
                "earliest_data_date": "19901219",
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T18:05:00",
                "status": "normal",
            }
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_columns",
        lambda engine, table_name: (
            [{"name": "trade_date", "type": "CHAR(8)"}]
            if engine is sentinel_engine
            else []
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_indexes",
        lambda engine, table_name: (
            [{"name": "PRIMARY", "columns": ["id"], "primary": True, "unique": True}]
            if engine is sentinel_engine
            else []
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_constraints",
        lambda engine, table_name: (
            [{"name": "pk_stock_daily", "type": "PRIMARY KEY", "columns": ["id"]}]
            if engine is sentinel_engine
            else []
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.table_detail_service.get_table_ddl",
        lambda engine, table_name: (
            "CREATE TABLE `stock_daily` (...)" if engine is sentinel_engine else ""
        ),
    )

    assert get_table_summary("stock_daily")["row_count"] == 5230000
    assert get_table_summary("stock_daily")["earliest_data_date"] == "19901219"
    assert get_table_structure("stock_daily") == {
        "columns": [{"name": "trade_date", "type": "CHAR(8)", "label": "交易日期"}],
        "indexes": [{"name": "PRIMARY", "columns": ["id"], "primary": True, "unique": True}],
        "constraints": [{"name": "pk_stock_daily", "type": "PRIMARY KEY", "columns": ["id"]}],
        "ddl": "CREATE TABLE `stock_daily` (...)",
    }

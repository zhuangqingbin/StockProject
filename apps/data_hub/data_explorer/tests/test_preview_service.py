import pytest

from apps.data_hub.data_explorer.backend.services.preview_service import (
    build_preview_queries,
    get_table_preview,
)


def test_build_preview_queries_uses_default_page_size_and_main_date_desc():
    result = build_preview_queries(
        table_name="stock_daily",
        columns=["ts_code", "trade_date", "open"],
        indexes=[["trade_date"], ["ts_code", "trade_date"]],
        page=1,
        filters={},
    )

    assert result["page_size"] == 50
    assert result["params"]["limit"] == 50
    assert result["params"]["offset"] == 0
    assert "ORDER BY trade_date DESC" in result["query"]


def test_build_preview_queries_caps_all_rows_without_offset():
    result = build_preview_queries(
        table_name="stock_daily",
        columns=["ts_code", "trade_date", "open"],
        indexes=[["trade_date"], ["ts_code", "trade_date"]],
        all_rows=True,
        filters={},
    )

    assert result["all_rows"] is True
    assert "LIMIT :all_rows_limit" in result["query"]
    assert "OFFSET" not in result["query"]
    assert result["params"]["all_rows_limit"] == 10000
    assert "offset" not in result["params"]


def test_build_preview_queries_falls_back_to_primary_or_first_index_when_no_date_column():
    result = build_preview_queries(
        table_name="job_run_log",
        columns=["id", "job_name", "status"],
        indexes=[["id"], ["job_name"]],
        page=2,
        filters={},
    )

    assert "ORDER BY id DESC" in result["query"]
    assert result["params"]["offset"] == 50


def test_build_preview_queries_accepts_date_and_ts_code_filters():
    result = build_preview_queries(
        table_name="stock_daily",
        columns=["ts_code", "trade_date", "open"],
        indexes=[["trade_date"], ["ts_code", "trade_date"]],
        filters={
            "trade_date_start": "20260301",
            "trade_date_end": "20260317",
            "ts_code": "000001.SZ",
        },
    )

    assert "trade_date >= :trade_date_start" in result["query"]
    assert "trade_date <= :trade_date_end" in result["query"]
    assert "ts_code = :ts_code" in result["query"]


def test_build_preview_queries_rejects_unsupported_filters():
    with pytest.raises(ValueError, match="Unsupported filter"):
        build_preview_queries(
            table_name="stock_daily",
            columns=["ts_code", "trade_date", "open"],
            indexes=[["trade_date"]],
            filters={"open": "10.5"},
        )


def test_get_table_preview_executes_parameterized_query_and_returns_rows(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
                "database_source": "ak",
            }
        },
        raising=False,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_engine",
        lambda source: sentinel_engine if source == "ak" else object(),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_columns",
        lambda engine, table_name: (
            [{"name": "ts_code"}, {"name": "trade_date"}, {"name": "open"}]
            if engine is sentinel_engine
            else []
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_indexes",
        lambda engine, table_name: (
            [{"name": "ix_trade_date", "columns": ["trade_date"]}]
            if engine is sentinel_engine
            else []
        ),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.run_preview_queries",
        lambda engine, query, count_query, params: (
            {
                "total": 1,
                "data": [{"ts_code": "000001.SZ", "trade_date": "20260317", "open": 12.3}],
            }
            if engine is sentinel_engine
            else {"total": 0, "data": []}
        ),
    )

    preview = get_table_preview("stock_daily", page=1, page_size=50, filters={"ts_code": "000001.SZ"})

    assert preview["columns"] == ["ts_code", "trade_date", "open"]
    assert preview["total"] == 1
    assert preview["data"][0]["ts_code"] == "000001.SZ"


def test_get_table_preview_marks_all_rows_mode_and_returns_full_dataset(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
            }
        },
        raising=False,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_engine",
        lambda source="ts": sentinel_engine,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_columns",
        lambda engine, table_name: [{"name": "ts_code"}, {"name": "trade_date"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_indexes",
        lambda engine, table_name: [{"name": "ix_trade_date", "columns": ["trade_date"]}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.run_preview_queries",
        lambda engine, query, count_query, params: {
            "total": 2,
            "data": [
                {"ts_code": "000001.SZ", "trade_date": "20260317"},
                {"ts_code": "000002.SZ", "trade_date": "20260316"},
            ],
        },
    )

    preview = get_table_preview("stock_daily", all_rows=True)

    assert preview["all_rows"] is True
    assert preview["truncated"] is False
    assert preview["truncated_limit"] == 10000
    assert preview["displayed_rows"] == 2
    assert preview["page"] == 1
    assert preview["page_size"] == 2
    assert len(preview["data"]) == 2


def test_get_table_preview_truncates_large_all_rows_result_to_first_10000(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
            }
        },
        raising=False,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_engine",
        lambda source="ts": sentinel_engine,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_columns",
        lambda engine, table_name: [{"name": "ts_code"}, {"name": "trade_date"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_indexes",
        lambda engine, table_name: [{"name": "ix_trade_date", "columns": ["trade_date"]}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.run_preview_queries",
        lambda engine, query, count_query, params: {
            "total": 12000,
            "data": [{"ts_code": "000001.SZ", "trade_date": "20260317"} for _ in range(10000)],
        },
    )

    preview = get_table_preview("stock_daily", all_rows=True)

    assert preview["all_rows"] is True
    assert preview["truncated"] is True
    assert preview["truncated_limit"] == 10000
    assert preview["displayed_rows"] == 10000
    assert preview["page_size"] == 10000
    assert len(preview["data"]) == 10000


def test_get_table_preview_rejects_unknown_table_outside_registry(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.preview_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
            }
        },
        raising=False,
    )

    with pytest.raises(KeyError, match="rogue_table"):
        get_table_preview("rogue_table")

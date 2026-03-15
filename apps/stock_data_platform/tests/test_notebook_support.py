from __future__ import annotations

from apps.stock_data_platform.jobs.runtime import JobDefinition
from apps.stock_data_platform.notebooks import notebook_support


def test_list_job_catalog_returns_expected_columns(monkeypatch):
    job_definitions = [
        JobDefinition(
            name="stock_daily",
            fetcher_cls=type("FakeDailyFetcher", (), {}),
            table_name="stock_daily",
            mirror_table_names=("daily_kline",),
            params={"trade_date": "{{ trade_date_compact }}"},
            scope_columns=("trade_date",),
            trigger_stock_bi_sync=True,
        )
    ]
    monkeypatch.setattr(notebook_support, "load_job_definitions", lambda config_path=None: job_definitions)

    frame = notebook_support.list_job_catalog()

    assert frame.to_dict("records") == [
        {
            "job_name": "stock_daily",
            "fetcher": "FakeDailyFetcher",
            "primary_table": "stock_daily",
            "mirror_tables": "daily_kline",
            "scope_columns": "trade_date",
            "trigger_stock_bi_sync": True,
        }
    ]


def test_preview_table_sql_quotes_identifier_and_limit():
    assert notebook_support.build_table_preview_sql("daily_kline", limit=10) == (
        "SELECT * FROM `daily_kline` LIMIT 10"
    )


def test_build_new_source_job_yaml_includes_mirror_scope_and_sync():
    snippet = notebook_support.build_new_source_job_yaml(
        name="custom_feature",
        fetcher="CustomFeatureFetch",
        table_name="stock_custom_feature",
        mirror_table_names=("bi_custom_feature",),
        params={"trade_date": "{{ trade_date_compact }}"},
        scope_columns=("trade_date",),
        trigger_stock_bi_sync=True,
    )

    assert "name: custom_feature" in snippet
    assert "fetcher: CustomFeatureFetch" in snippet
    assert "table_name: stock_custom_feature" in snippet
    assert "mirror_table_names:" in snippet
    assert "- bi_custom_feature" in snippet
    assert "trigger_stock_bi_sync: true" in snippet
    assert "scope_columns:" in snippet
    assert "- trade_date" in snippet

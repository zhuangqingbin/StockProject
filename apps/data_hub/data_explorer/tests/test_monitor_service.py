from apps.data_hub.data_explorer.backend.services.monitor_service import (
    get_latest_job_runs,
    get_monitor_overview,
    list_job_monitor_rows,
    list_pipeline_run_rows,
    list_table_recent_runs,
    list_table_monitor_rows,
)


def test_list_table_monitor_rows_returns_table_status_rows(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
                "description": "A股日线行情",
                "job_name": "stock_daily",
                "trigger_profile": "trade_day_post_close_core",
            }
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_table_stats",
        lambda table_names: {
            "stock_daily": {
                "row_count": 5230000,
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T18:05:00",
                "status": "normal",
            }
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_latest_job_runs",
        lambda: {
            "stock_daily": {
                "result": "success",
                "run_id": "run-001",
            }
        },
    )

    rows = list_table_monitor_rows()

    assert rows == [
        {
            "table_name": "stock_daily",
            "category": "stock_market_data",
            "latest_data_date": "20260317",
            "last_updated": "2026-03-17T18:05:00",
            "freshness": "normal",
            "trigger_profile": "trade_day_post_close_core",
            "last_run_result": "success",
            "last_run_id": "run-001",
        }
    ]


def test_list_job_monitor_rows_returns_latest_job_runs(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
                "description": "A股日线行情",
                "job_name": "stock_daily",
                "trigger_profile": "trade_day_post_close_core",
            }
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_latest_job_runs",
        lambda: {
            "stock_daily": {
                "status": "success",
                "executed_at": "2026-03-17T18:05:00",
                "duration_seconds": 12.3,
                "error": None,
            }
        },
    )

    rows = list_job_monitor_rows()

    assert rows == [
        {
            "run_id": None,
            "run_mode": None,
            "trigger_profile": "trade_day_post_close_core",
            "job_name": "stock_daily",
            "table_name": "stock_daily",
            "result": "success",
            "status": "success",
            "effective_date": None,
            "executed_at": "2026-03-17T18:05:00",
            "duration_seconds": 12.3,
            "rows_written": None,
            "error": None,
        }
    ]


def test_get_latest_job_runs_reads_runtime_table_when_available(monkeypatch):
    sentinel_engine = object()

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_engine",
        lambda source: sentinel_engine if source == "ts" else object(),
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_latest_job_run_rows",
        lambda engine: [
            {
                "job_name": "stock_daily",
                "status": "success",
                "executed_at": "2026-03-17T18:05:00",
                "duration_seconds": 12.3,
                "error": None,
            }
        ],
    )

    latest = get_latest_job_runs()["stock_daily"]

    assert latest["status"] == "success"
    assert latest["result"] == "success"
    assert latest["job_name"] == "stock_daily"


def test_list_pipeline_run_rows_groups_recent_job_runs(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_recent_job_runs",
        lambda limit=200: [
            {
                "run_id": "run-001",
                "run_mode": "once",
                "trigger_profile": "trade_day_post_close_core",
                "job_name": "stock_daily",
                "table_name": "stock_daily",
                "result": "success",
                "effective_date": "20260317",
                "executed_at": "2026-03-17 18:05:00",
                "_executed_at_dt": None,
            },
            {
                "run_id": "run-001",
                "run_mode": "once",
                "trigger_profile": "trade_day_post_close_core",
                "job_name": "stock_daily_basic",
                "table_name": "stock_daily_basic",
                "result": "failed",
                "effective_date": "20260317",
                "executed_at": "2026-03-17 18:06:00",
                "_executed_at_dt": None,
            },
        ],
    )

    rows = list_pipeline_run_rows()

    assert rows == [
        {
            "run_id": "run-001",
            "run_mode": "once",
            "status": "partial_failed",
            "trigger_profiles": ["trade_day_post_close_core"],
            "job_count": 2,
            "failed_jobs": 1,
            "successful_jobs": 1,
            "table_count": 2,
            "effective_window": "20260317",
            "started_at": None,
            "ended_at": None,
        }
    ]


def test_list_table_recent_runs_filters_runs_by_table(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_recent_job_runs",
        lambda limit=400: [
            {
                "run_id": "run-001",
                "run_mode": "once",
                "trigger_profile": "trade_day_post_close_core",
                "job_name": "stock_daily",
                "table_name": "stock_daily",
                "result": "success",
                "effective_date": "20260317",
                "executed_at": "2026-03-17 18:05:00",
                "duration_seconds": 12.3,
                "rows_written": 10,
                "error": None,
            },
            {
                "run_id": "run-002",
                "run_mode": "once",
                "trigger_profile": "trade_day_post_close_core",
                "job_name": "stock_daily_basic",
                "table_name": "stock_daily_basic",
                "result": "success",
                "effective_date": "20260317",
                "executed_at": "2026-03-17 18:06:00",
                "duration_seconds": 10.0,
                "rows_written": 12,
                "error": None,
            },
        ],
    )

    assert list_table_recent_runs("stock_daily") == [
        {
            "run_id": "run-001",
            "run_mode": "once",
            "trigger_profile": "trade_day_post_close_core",
            "job_name": "stock_daily",
            "result": "success",
            "effective_date": "20260317",
            "executed_at": "2026-03-17 18:05:00",
            "duration_seconds": 12.3,
            "rows_written": 10,
            "error": None,
        }
    ]


def test_get_monitor_overview_summarizes_dataset_and_run_metrics(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_table_registry",
        lambda: {
            "stock_daily": {
                "table_name": "stock_daily",
                "category": "stock_market_data",
            },
            "stock_daily_basic": {
                "table_name": "stock_daily_basic",
                "category": "stock_market_data",
            },
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_table_stats",
        lambda table_names: {
            "stock_daily": {"status": "normal"},
            "stock_daily_basic": {"status": "delayed"},
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.get_recent_job_runs",
        lambda limit=400: [
            {
                "run_id": "run-001",
                "run_mode": "once",
                "trigger_profile": "trade_day_post_close_core",
                "job_name": "stock_daily",
                "table_name": "stock_daily",
                "result": "failed",
                "_executed_at_dt": None,
            }
        ],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.monitor_service.list_pipeline_run_rows",
        lambda limit=50, recent_job_runs=None: [
            {
                "run_id": "run-001",
                "run_mode": "once",
                "status": "failed",
                "trigger_profiles": ["trade_day_post_close_core"],
                "job_count": 1,
                "failed_jobs": 1,
                "successful_jobs": 0,
                "table_count": 1,
                "effective_window": "20260317",
                "started_at": "2026-03-17 18:05:00",
                "ended_at": "2026-03-17 18:05:00",
            }
        ],
    )

    overview = get_monitor_overview()

    assert overview["dataset_count"] == 2
    assert overview["fresh_datasets"] == 1
    assert overview["delayed_datasets"] == 1
    assert overview["recent_failed_jobs"] == 1
    assert overview["latest_run"]["run_id"] == "run-001"

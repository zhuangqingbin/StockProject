from fastapi.testclient import TestClient

from apps.data_hub.data_explorer.backend.main import create_app


def test_create_app_exposes_health_endpoint():
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_app_exposes_catalog_endpoints(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.catalog.list_categories",
        lambda: [{"key": "basic_data", "label": "Basic Data", "table_count": 6}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.catalog.list_tables_by_category",
        lambda category_key: [
            {
                "table_name": "stock_basic",
                "category": category_key,
                "description": "A股基础信息",
                "row_count": 5400,
                "earliest_data_date": "19910403",
                "latest_data_date": "20260317",
                "last_updated": "2026-03-17T09:25:00",
                "status": "normal",
            }
        ],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.catalog.get_table_detail",
        lambda table_name: {
            "table_name": table_name,
            "category": "basic_data",
            "description": "A股基础信息",
            "summary": {"row_count": 5400, "earliest_data_date": "19910403", "latest_data_date": "20260317"},
            "structure": {"columns": [], "indexes": [], "constraints": [], "ddl": ""},
        },
    )

    client = TestClient(create_app())

    categories = client.get("/api/catalog/categories")
    tables = client.get("/api/catalog/categories/basic_data/tables")
    detail = client.get("/api/catalog/tables/stock_basic")

    assert categories.status_code == 200
    assert categories.json()[0]["table_count"] == 6
    assert tables.status_code == 200
    assert tables.json()[0]["table_name"] == "stock_basic"
    assert tables.json()[0]["earliest_data_date"] == "19910403"
    assert detail.status_code == 200
    assert detail.json()["table_name"] == "stock_basic"
    assert detail.json()["summary"]["earliest_data_date"] == "19910403"


def test_create_app_exposes_preview_monitor_and_database_metadata_endpoints(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.preview.get_table_preview",
        lambda table_name, page=1, page_size=50, filters=None, all_rows=False: {
            "table_name": table_name,
            "page": page,
            "page_size": page_size,
            "total": 100,
            "all_rows": all_rows,
            "displayed_rows": 100 if all_rows else 50,
            "truncated": all_rows,
            "truncated_limit": 10000 if all_rows else None,
            "data": [{"id": 1}],
        },
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.monitor.get_monitor_overview",
        lambda: {"dataset_count": 48, "recent_runs": 3, "latest_run": {"run_id": "run-001"}},
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.monitor.list_table_monitor_rows",
        lambda: [{"table_name": "stock_daily", "freshness": "normal"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.monitor.list_job_monitor_rows",
        lambda: [{"job_name": "stock_daily", "result": "success"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.monitor.list_pipeline_run_rows",
        lambda: [{"run_id": "run-001", "status": "success"}],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.database_metadata.get_schema_overview",
        lambda: {"table_count": 48, "runtime_table_count": 1, "category_counts": {"basic_data": 6}},
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.database_metadata.get_table_metadata_detail",
        lambda table_name: {
            "columns": [{"name": "trade_date"}],
            "indexes": [{"name": "PRIMARY"}],
            "constraints": [{"name": "pk_stock_daily"}],
            "ddl": "CREATE TABLE `stock_daily` (...)",
        },
    )

    client = TestClient(create_app())

    preview = client.get("/api/preview/stock_daily")
    preview_all = client.get("/api/preview/stock_daily?all_rows=true")
    monitor_overview = client.get("/api/monitor/overview")
    monitor_tables = client.get("/api/monitor/tables")
    monitor_jobs = client.get("/api/monitor/jobs")
    monitor_runs = client.get("/api/monitor/runs")
    overview = client.get("/api/database/overview")
    metadata = client.get("/api/database/tables/stock_daily/metadata")

    assert preview.status_code == 200
    assert preview.json()["page_size"] == 50
    assert preview_all.status_code == 200
    assert preview_all.json()["all_rows"] is True
    assert preview_all.json()["truncated"] is True
    assert preview_all.json()["truncated_limit"] == 10000
    assert monitor_overview.status_code == 200
    assert monitor_overview.json()["dataset_count"] == 48
    assert monitor_tables.status_code == 200
    assert monitor_tables.json()[0]["table_name"] == "stock_daily"
    assert monitor_jobs.status_code == 200
    assert monitor_jobs.json()[0]["job_name"] == "stock_daily"
    assert monitor_runs.status_code == 200
    assert monitor_runs.json()[0]["run_id"] == "run-001"
    assert overview.status_code == 200
    assert overview.json()["table_count"] == 48
    assert metadata.status_code == 200
    assert metadata.json()["ddl"] == "CREATE TABLE `stock_daily` (...)"


def test_create_app_returns_not_found_for_unknown_catalog_table(monkeypatch):
    def raise_missing_table(table_name: str):
        raise KeyError(table_name)

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.catalog.get_table_detail",
        raise_missing_table,
    )

    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/api/catalog/tables/rogue_table")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown table: rogue_table"


def test_create_app_returns_not_found_for_unknown_preview_table(monkeypatch):
    def raise_missing_table(
        table_name: str,
        page: int = 1,
        page_size: int = 50,
        filters: dict[str, str] | None = None,
        all_rows: bool = False,
    ):
        raise KeyError(table_name)

    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.api.preview.get_table_preview",
        raise_missing_table,
    )

    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/api/preview/rogue_table")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown table: rogue_table"

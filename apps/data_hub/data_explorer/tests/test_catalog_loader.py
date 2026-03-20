import pytest

from apps.data_hub.data_explorer.backend.infrastructure.catalog_loader import load_table_catalog


def test_load_table_catalog_returns_expected_labels_and_runtime_entries():
    catalog = load_table_catalog()

    assert catalog.categories["stock_market_data"].label == "Stock Market Data"
    assert catalog.tables["stock_daily"].category == "stock_market_data"
    assert catalog.tables["stock_daily"].description == "A股日线行情"
    assert catalog.tables["stock_basic"].description == "A股基础信息"
    assert catalog.tables["job_run_log"].category == "runtime"
    assert catalog.tables["job_run_log"].description == "任务执行日志"
    assert "precomputed_market" in catalog.excluded_tables


def test_load_table_catalog_rejects_table_category_without_declaration(tmp_path):
    catalog_path = tmp_path / "table_catalog.yaml"
    catalog_path.write_text(
        """
categories:
  basic_data:
    label: "Basic Data"

tables:
  stock_daily:
    category: ghost_data
    description: "A股日线行情"
""".strip(),
        encoding="utf-8",
    )

    load_table_catalog.cache_clear()

    with pytest.raises(ValueError, match="unknown category"):
        load_table_catalog(str(catalog_path))

    load_table_catalog.cache_clear()

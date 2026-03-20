import pytest

from apps.data_hub.data_explorer.backend.infrastructure.db import build_mysql_url
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    extract_create_table_sql,
    normalize_columns,
    normalize_indexes,
)
from apps.data_hub.data_explorer.backend.services.database_metadata_service import (
    get_schema_overview,
    get_table_metadata_detail,
)


def test_build_mysql_url_uses_source_specific_database(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "demo")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_HOST", "db.local")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("TS_MYSQL_DATABASE", "stock_database_ts")
    monkeypatch.setenv("AK_MYSQL_DATABASE", "stock_database_ak")
    monkeypatch.setenv("MYSQL_CHARSET", "utf8mb4")

    assert (
        build_mysql_url("ts")
        == "mysql+pymysql://demo:secret@db.local:3307/stock_database_ts?charset=utf8mb4"
    )
    assert (
        build_mysql_url("ak")
        == "mysql+pymysql://demo:secret@db.local:3307/stock_database_ak?charset=utf8mb4"
    )


def test_build_mysql_url_requires_selected_source_database(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "demo")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_HOST", "db.local")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_CHARSET", "utf8mb4")
    monkeypatch.setenv("TS_MYSQL_DATABASE", "stock_database_ts")
    monkeypatch.delenv("AK_MYSQL_DATABASE", raising=False)

    with pytest.raises(ValueError, match="AK_MYSQL_DATABASE"):
        build_mysql_url("ak")


def test_normalize_columns_keeps_comment_and_nullable():
    columns = normalize_columns(
        [
            {
                "name": "trade_date",
                "type": "CHAR(8)",
                "nullable": False,
                "default": None,
                "comment": "交易日期",
            }
        ]
    )

    assert columns == [
        {
            "name": "trade_date",
            "type": "CHAR(8)",
            "nullable": False,
            "default": None,
            "comment": "交易日期",
        }
    ]


def test_normalize_indexes_marks_primary_and_unique():
    indexes = normalize_indexes(
        indexes=[
            {"name": "ix_trade_date", "column_names": ["trade_date"], "unique": False},
            {"name": "uq_code_date", "column_names": ["ts_code", "trade_date"], "unique": True},
        ],
        primary_key={"constrained_columns": ["id"], "name": "PRIMARY"},
    )

    assert indexes == [
        {"name": "PRIMARY", "columns": ["id"], "unique": True, "primary": True},
        {"name": "ix_trade_date", "columns": ["trade_date"], "unique": False, "primary": False},
        {"name": "uq_code_date", "columns": ["ts_code", "trade_date"], "unique": True, "primary": False},
    ]


def test_extract_create_table_sql_returns_mysql_statement():
    ddl = extract_create_table_sql(
        {
            "Table": "stock_daily",
            "Create Table": "CREATE TABLE `stock_daily` (`trade_date` char(8))",
        }
    )

    assert ddl == "CREATE TABLE `stock_daily` (`trade_date` char(8))"


def test_get_schema_overview_counts_tables_and_categories(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.database_metadata_service.get_table_registry",
        lambda: {
            "stock_daily": {"category": "stock_market_data"},
            "stock_basic": {"category": "basic_data"},
            "job_run_log": {"category": "runtime"},
        },
    )

    overview = get_schema_overview()

    assert overview["table_count"] == 3
    assert overview["category_counts"]["stock_market_data"] == 1
    assert overview["category_counts"]["basic_data"] == 1
    assert overview["runtime_table_count"] == 1


def test_get_table_metadata_detail_returns_structure_sections(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.database_metadata_service.get_table_detail",
        lambda table_name: {
            "table_name": table_name,
            "structure": {
                "columns": [{"name": "trade_date"}],
                "indexes": [{"name": "PRIMARY"}],
                "constraints": [{"name": "pk_stock_daily"}],
                "ddl": "CREATE TABLE `stock_daily` (...)",
            },
        },
    )

    detail = get_table_metadata_detail("stock_daily")

    assert detail["columns"] == [{"name": "trade_date"}]
    assert detail["indexes"] == [{"name": "PRIMARY"}]
    assert detail["constraints"] == [{"name": "pk_stock_daily"}]
    assert detail["ddl"] == "CREATE TABLE `stock_daily` (...)"


def test_get_schema_overview_includes_current_schema_name(monkeypatch):
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.database_metadata_service.get_table_registry",
        lambda: {"stock_daily": {"category": "stock_market_data"}},
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.database_metadata_service.get_current_schema_name",
        lambda engine: {
            "ts_engine": "stock_database_ts",
            "ak_engine": "stock_database_ak",
        }[engine],
    )
    monkeypatch.setattr(
        "apps.data_hub.data_explorer.backend.services.database_metadata_service.get_engine",
        lambda source: f"{source}_engine",
    )

    overview = get_schema_overview()

    assert overview["schema_name"] == "stock_database_ts"
    assert overview["schema_names"] == {
        "ts": "stock_database_ts",
        "ak": "stock_database_ak",
    }

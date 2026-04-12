from pathlib import Path

from apps.quant_platform.research.config import ResearchConfig, build_tushare_db_url


def test_research_config_defaults_match_requirements():
    config = ResearchConfig()

    assert config.start_date == "2018-01-01"
    assert config.database_env_name == "TS_MYSQL_DATABASE"
    assert config.panel_table == "stock_stk_factor_pro"
    assert config.output_dir == Path("apps/quant_platform/research/output")


def test_build_tushare_db_url_uses_shared_stock_core_env(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "quant")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_CHARSET", "utf8mb4")
    monkeypatch.setenv("TS_MYSQL_DATABASE", "tushare_database")

    url = build_tushare_db_url()

    assert url == "mysql+pymysql://quant:secret@localhost:3306/tushare_database?charset=utf8mb4"

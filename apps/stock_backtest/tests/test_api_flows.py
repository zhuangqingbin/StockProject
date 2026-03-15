from datetime import date, timedelta

from fastapi.testclient import TestClient

from apps.stock_backtest.backend.infrastructure.database import get_session_factory, reset_database
from apps.stock_backtest.backend.infrastructure.settings import get_settings
from apps.stock_backtest.backend.main import create_app
from apps.stock_backtest.backend.modules.data.service import normalize_market_trade_date
from apps.stock_backtest.backend.models.db_models import MarketIndexDailyModel


def _seed_market_data(client: TestClient):
    base_day = date(2025, 1, 2)
    rows = []
    for offset in range(40):
        trade_day = base_day + timedelta(days=offset)
        rows.append(
            {
                "ts_code": "000001.SZ",
                "trade_date": trade_day.isoformat(),
                "open": 10 + offset * 0.12,
                "high": 10.3 + offset * 0.12,
                "low": 9.8 + offset * 0.12,
                "close": 10.1 + offset * 0.16,
                "vol": 100000 + offset * 2000,
                "amount": 1000000 + offset * 50000,
            }
        )

    payload = {
        "symbols": [
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "industry": "银行",
                "market": "主板",
            }
        ],
        "daily_kline": rows,
    }
    response = client.post("/api/dev/seed", json=payload)
    assert response.status_code == 200


def _seed_index_data():
    session = get_session_factory()()
    try:
        session.merge(
            MarketIndexDailyModel(
                ts_code="000300.SH",
                trade_date=date(2025, 2, 10),
                close=3988.0,
            )
        )
        session.merge(
            MarketIndexDailyModel(
                ts_code="000905.SH",
                trade_date=date(2025, 2, 10),
                close=6122.0,
            )
        )
        session.commit()
    finally:
        session.close()


def test_strategy_run_and_analysis_flow(monkeypatch, tmp_path):
    database_path = tmp_path / "stock-backtest.sqlite3"

    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", "")
    monkeypatch.setenv("STOCK_BACKTEST_EXECUTION_MODE", "inline")

    get_settings.cache_clear()
    reset_database()
    app = create_app()
    client = TestClient(app)

    _seed_market_data(client)
    _seed_index_data()

    templates = client.get("/api/strategies/templates")
    assert templates.status_code == 200
    assert any(item["template_id"] == "ma_crossover" for item in templates.json())

    strategy = client.post(
        "/api/strategies",
        json={
            "name": "双均线样例",
            "description": "测试策略",
            "source_type": "template",
            "template_id": "ma_crossover",
            "default_params": {"fast_period": 3, "slow_period": 8},
            "required_feeds": ["daily_kline"],
            "author": "codex",
        },
    )
    assert strategy.status_code == 201
    strategy_id = strategy.json()["id"]

    run_payload = {
        "strategy_id": strategy_id,
        "params": {"fast_period": 3, "slow_period": 8},
        "symbols": ["000001.SZ"],
        "start_date": "2025-01-02",
        "end_date": "2025-02-10",
        "initial_cash": 100000,
        "commission_rate": 0.0003,
        "benchmark": "000300.SH",
        "data_feeds": ["daily_kline"],
        "submitted_by": "codex",
    }

    run = client.post(
        "/api/backtest/run",
        json=run_payload,
    )
    assert run.status_code == 202
    run_id = run.json()["run_id"]
    assert run.json()["cache_hit"] is False
    assert run.json()["reused_from_run_id"] is None

    run_detail = client.get(f"/api/backtest/runs/{run_id}")
    assert run_detail.status_code == 200
    assert run_detail.json()["status"] == "completed"
    assert run_detail.json()["metrics"]["total_return"] is not None
    assert run_detail.json()["cache_hit"] is False
    assert run_detail.json()["request_signature"]

    diagnostics = client.get(f"/api/backtest/runs/{run_id}/diagnostics")
    assert diagnostics.status_code == 200
    assert diagnostics.json()["run_id"] == run_id
    assert diagnostics.json()["cache_hit"] is False
    assert any(event["stage"] == "completed" for event in diagnostics.json()["events"])

    daily = client.get(f"/api/analysis/{run_id}/daily")
    assert daily.status_code == 200
    assert len(daily.json()) > 5

    trades = client.get(f"/api/analysis/{run_id}/trades")
    assert trades.status_code == 200

    compare = client.get(f"/api/analysis/compare?run_ids={run_id}")
    assert compare.status_code == 200
    assert compare.json()["runs"][0]["run_id"] == run_id

    cached_run = client.post("/api/backtest/run", json=run_payload)
    assert cached_run.status_code == 202
    assert cached_run.json()["cache_hit"] is True
    cached_run_id = cached_run.json()["run_id"]
    assert cached_run_id != run_id
    assert cached_run.json()["reused_from_run_id"] == run_id

    cached_run_detail = client.get(f"/api/backtest/runs/{cached_run_id}")
    assert cached_run_detail.status_code == 200
    assert cached_run_detail.json()["status"] == "completed"
    assert cached_run_detail.json()["cache_hit"] is True
    assert cached_run_detail.json()["reused_from_run_id"] == run_id

    cached_diagnostics = client.get(f"/api/backtest/runs/{cached_run_id}/diagnostics")
    assert cached_diagnostics.status_code == 200
    assert cached_diagnostics.json()["cache_hit"] is True
    assert cached_diagnostics.json()["reused_from_run_id"] == run_id
    assert any(event["stage"] == "cache_hit" for event in cached_diagnostics.json()["events"])

    cached_daily = client.get(f"/api/analysis/{cached_run_id}/daily")
    assert cached_daily.status_code == 200
    assert len(cached_daily.json()) == len(daily.json())

    runtime = client.get("/api/backtest/runtime")
    assert runtime.status_code == 200
    assert runtime.json()["execution_mode"] == "inline"
    assert runtime.json()["status_counts"]["completed"] == 2
    assert runtime.json()["cache_hits"] == 1
    assert runtime.json()["active_run_ids"] == []

    symbols = client.get("/api/data/symbols", params={"keyword": "平安"})
    assert symbols.status_code == 200
    assert symbols.json()[0]["ts_code"] == "000001.SZ"

    data_overview = client.get("/api/data/overview")
    assert data_overview.status_code == 200
    assert data_overview.json()["symbol_count"] >= 1
    assert data_overview.json()["benchmark_count"] == 2
    assert any(item["feed_id"] == "daily_kline" for item in data_overview.json()["feed_health"])
    daily_kline_health = next(item for item in data_overview.json()["feed_health"] if item["feed_id"] == "daily_kline")
    assert daily_kline_health["earliest_trade_date"] == "2025-01-02"
    assert daily_kline_health["latest_trade_date"] == "2025-02-10"

    benchmarks = client.get("/api/data/benchmarks")
    assert benchmarks.status_code == 200
    assert [item["ts_code"] for item in benchmarks.json()] == ["000300.SH", "000905.SH"]

    filtered_symbols = client.get("/api/data/symbols", params={"industry": "银行"})
    assert filtered_symbols.status_code == 200
    assert filtered_symbols.json()[0]["industry"] == "银行"


def test_normalize_market_trade_date_handles_mysql_string_dates():
    assert normalize_market_trade_date("20260212").isoformat() == "2026-02-12"
    assert normalize_market_trade_date("2026-02-12").isoformat() == "2026-02-12"
    assert normalize_market_trade_date(None) is None

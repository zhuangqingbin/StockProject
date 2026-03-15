import math

from apps.stock_backtest.backend.engine.data_registry import get_feed_catalog
from apps.stock_backtest.backend.engine.metrics import calculate_performance_metrics
from apps.stock_backtest.backend.engine.strategy_loader import (
    clear_strategy_template_cache,
    get_strategy_template,
    list_strategy_templates,
)


def test_template_catalog_contains_v1_templates():
    template_ids = {item.template_id for item in list_strategy_templates()}

    assert {
        "ma_crossover",
        "breakout",
        "mean_reversion",
        "momentum",
        "money_flow",
        "rsi_rotation",
        "bollinger_reversion",
        "volume_breakout",
        "atr_trend_following",
    } <= template_ids

    template = get_strategy_template("ma_crossover")
    assert template.required_feeds == ["daily_kline"]
    assert "fast_period" in template.parameters

    atr_template = get_strategy_template("atr_trend_following")
    assert "atr_period" in atr_template.parameters
    assert atr_template.required_feeds == ["daily_kline"]


def test_template_catalog_is_cached_between_calls():
    clear_strategy_template_cache()

    first_pass = list_strategy_templates()
    second_pass = list_strategy_templates()

    assert first_pass is second_pass


def test_feed_catalog_contains_expected_market_tables():
    feed_ids = {item.feed_id for item in get_feed_catalog()}

    assert {"daily_kline", "daily_basic", "moneyflow", "index_daily", "top_list", "stock_basic"} <= feed_ids


def test_calculate_performance_metrics_from_equity_curve():
    equity_curve = [
        {"trade_date": "2025-01-02", "portfolio_value": 100000.0, "cash": 20000.0},
        {"trade_date": "2025-01-03", "portfolio_value": 102000.0, "cash": 20000.0},
        {"trade_date": "2025-01-06", "portfolio_value": 101000.0, "cash": 19000.0},
        {"trade_date": "2025-01-07", "portfolio_value": 106500.0, "cash": 21000.0},
    ]

    metrics = calculate_performance_metrics(equity_curve)

    assert round(metrics["total_return"], 4) == 0.065
    assert metrics["max_drawdown"] < 0
    assert metrics["annual_return"] > 0
    assert not math.isnan(metrics["sharpe_ratio"])
    assert metrics["trading_days"] == 4

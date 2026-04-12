import math

import pandas as pd

from apps.quant_platform.research.data_loader import (
    ResearchDataLoader,
    _normalize_query_date,
    apply_available_lag,
    build_forward_overnight_returns,
)
from apps.quant_platform.research.universe import UniverseFilter, UniverseFilterConfig


def test_apply_available_lag_shifts_columns_within_each_stock():
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "north_hold_ratio": 0.10},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "north_hold_ratio": 0.20},
            {"ts_code": "000002.SZ", "trade_date": "2026-01-02", "north_hold_ratio": 0.30},
            {"ts_code": "000002.SZ", "trade_date": "2026-01-03", "north_hold_ratio": 0.40},
        ]
    )

    shifted = apply_available_lag(panel, {"north_hold_ratio": 1})

    assert math.isnan(shifted.loc[0, "north_hold_ratio"])
    assert shifted.loc[1, "north_hold_ratio"] == 0.10
    assert math.isnan(shifted.loc[2, "north_hold_ratio"])
    assert shifted.loc[3, "north_hold_ratio"] == 0.30


def test_build_forward_overnight_returns_uses_next_open_and_current_close():
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "close": 10.0, "open": 10.5},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "close": 10.2, "open": 10.8},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-06", "close": 10.4, "open": 10.6},
        ]
    )

    enriched = build_forward_overnight_returns(panel)

    assert round(enriched.loc[0, "overnight_return"], 10) == 0.08
    assert round(enriched.loc[1, "overnight_return"], 6) == round((10.6 - 10.2) / 10.2, 6)
    assert math.isnan(enriched.loc[2, "overnight_return"])


def test_research_data_loader_prepare_panel_sorts_then_builds_target():
    loader = ResearchDataLoader()
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "close": 10.2, "open": 10.8},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "close": 10.0, "open": 10.5},
        ]
    )

    prepared = loader.prepare_panel(panel)

    assert prepared["trade_date"].tolist() == ["2026-01-02", "2026-01-03"]
    assert round(prepared.loc[0, "overnight_return"], 10) == 0.08


def test_universe_filter_excludes_st_suspended_and_recent_ipo():
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-10", "close": 10.0},
            {"ts_code": "000002.SZ", "trade_date": "2026-01-10", "close": 12.0},
            {"ts_code": "000003.SZ", "trade_date": "2026-01-10", "close": 14.0},
            {"ts_code": "000004.SZ", "trade_date": "2026-01-10", "close": 16.0},
        ]
    )
    stock_basic = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "list_date": "2010-01-01"},
            {"ts_code": "000002.SZ", "list_date": "2010-01-01"},
            {"ts_code": "000003.SZ", "list_date": "2025-12-15"},
            {"ts_code": "000004.SZ", "list_date": "2010-01-01"},
        ]
    )
    st_flags = pd.DataFrame([{"ts_code": "000002.SZ", "trade_date": "2026-01-10"}])
    suspensions = pd.DataFrame([{"ts_code": "000004.SZ", "trade_date": "2026-01-10", "suspend_type": "S"}])

    filtered = UniverseFilter(UniverseFilterConfig(min_list_days=60)).apply(
        panel=panel,
        stock_basic=stock_basic,
        st_flags=st_flags,
        suspensions=suspensions,
    )

    assert filtered["ts_code"].tolist() == ["000001.SZ"]


def test_normalize_query_date_matches_tushare_trade_date_format():
    assert _normalize_query_date("2024-01-01") == "20240101"
    assert _normalize_query_date("20240131") == "20240131"

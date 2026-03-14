from datetime import date
from decimal import Decimal

from apps.stock_bi.codex.backend.modules.market_summary.application import (
    build_amount_trend_rows,
    build_indices_payload,
    build_industry_flow_payload,
    build_industry_ranking_payload,
    build_industries_enhanced_payload,
    build_latest_date_payload,
    build_limit_stats_payload,
    build_limit_trend_rows,
    build_overview_payload,
    build_sectors_enhanced_payload,
    build_summary_payload,
    build_top_list_summary_payload,
    format_date,
    normalize_trade_date,
)
from apps.stock_bi.codex.backend.modules.ranking_kline.application import (
    build_industry_stocks_payload,
    build_kline_rows,
    build_moneyflow_payload,
    build_ranking_enhanced_payload,
    build_search_results,
    filter_market_rows,
    select_ranking_rows,
    to_float,
)
from apps.stock_bi.codex.backend.modules.realtime_updates.service import (
    build_connected_message,
    build_data_updated_message,
    build_status_message,
)


def test_normalize_trade_date_uses_latest_when_missing():
    assert normalize_trade_date(None, latest_trade_date="20250314") == "20250314"
    assert normalize_trade_date("2025-03-14") == "20250314"


def test_format_date_handles_strings_and_dates():
    assert format_date("20250314") == "2025-03-14"
    assert format_date(date(2025, 3, 14)) == "2025-03-14"


def test_market_payload_builders_preserve_shape():
    summary = {
        "total_stocks": 10,
        "up_count": 6,
        "down_count": 4,
        "flat_count": 0,
        "limit_up": 1,
        "limit_down": 0,
        "total_amount": 12.3,
        "avg_pct_chg": 1.23,
    }
    consistency = {"consistent": True, "primary_date": "20250314", "warnings": []}

    latest = build_latest_date_payload("20250314")
    overview = build_overview_payload("20250314", summary)
    payload = build_summary_payload("20250314", summary, consistency)

    assert latest == {"latest_date": "2025-03-14", "raw_date": "20250314"}
    assert overview["trade_date"] == "2025-03-14"
    assert payload["data_consistency"]["consistent"] is True


def test_summary_derived_payload_builders_cover_fallbacks():
    summary = {
        "top_list_summary": {"count": 3, "net_amount": 8.8},
        "index_data": [{"ts_code": "000001.SH"}],
        "industry_ranking": [{"name": "半导体"}, {"name": "银行"}],
        "industry_stats": [{"industry": "半导体"}],
        "limit_stats": None,
        "limit_up": 5,
        "limit_down": 1,
    }

    top_list = build_top_list_summary_payload("20250314", summary)
    indices = build_indices_payload("20250314", summary)
    industries = build_industry_ranking_payload("20250314", summary, limit=1)
    flow = build_industry_flow_payload("20250314", summary)
    limit_stats = build_limit_stats_payload("20250314", summary)

    assert top_list["count"] == 3
    assert indices["indices"] == [{"ts_code": "000001.SH"}]
    assert industries["industries"] == [{"name": "半导体"}]
    assert flow["industries"] == [{"industry": "半导体"}]
    assert limit_stats["limit_up"] == 5
    assert limit_stats["limit_down"] == 1


def test_ranking_helpers_filter_and_select_expected_rows():
    summary = {
        "top_gainers": [{"ts_code": "688001.SH"}, {"ts_code": "000001.SZ"}],
        "top_losers": [{"ts_code": "300001.SZ"}],
        "top_amount": [{"ts_code": "600001.SH"}],
        "top_turnover": [{"ts_code": "830001.BJ"}],
    }

    assert select_ranking_rows(summary, sort_by="amount", order="desc") == [{"ts_code": "600001.SH"}]
    assert filter_market_rows(summary["top_gainers"], "科创板") == [{"ts_code": "688001.SH"}]
    assert filter_market_rows(summary["top_gainers"], "未知市场") == summary["top_gainers"]


def test_row_mapping_helpers_keep_market_response_shapes():
    amount_rows = [("20250313", 12.345), ("20250314", 8.8)]
    limit_rows = [("20250313", 10, 2), ("20250314", None, 1)]
    kline_rows = [
        ("000001.SZ", "20250314", 10, 11, 9, 10.5, 1.2, 1000, 2000),
        ("000001.SZ", "20250313", 9, 10, 8, 9.5, -0.2, 900, 1800),
    ]
    search_rows = [("000001.SZ", None), ("600000.SH", "浦发银行")]

    amount = build_amount_trend_rows(amount_rows)
    limit = build_limit_trend_rows(limit_rows)
    kline = build_kline_rows(kline_rows)
    search = build_search_results(search_rows)

    assert amount[0]["trade_date"] == "2025-03-14"
    assert amount[0]["total_amount"] == 8.8
    assert limit[1]["limit_up"] == 10
    assert kline[0]["date"] == "2025-03-13"
    assert search[0]["name"] == "000001.SZ"


def test_enhanced_payload_builders_keep_existing_fields():
    sectors_rows = [
        ("其他", 0.1, 1.0, 1, 1, 0, 0, 0, 0),
        ("科创板", 1.2, 8.8, 4, 3, 1, 0, 1, 0),
    ]
    industries_rows = [("半导体", 1.2, 10.1, 4, 3, 1)]
    ranking_rows = [("000001.SZ", None, 1.2, 10.5, 88.8, 120000, 3.1, "银行", 8.1, 0.9)]
    stocks_rows = [("000001.SZ", None, 1.2, 10.5, 10.0, 10.8, 9.8, 12.3, 88.8, 3.1, 8.1, 0.9, 100.0)]
    moneyflow_row = (
        "000001.SZ", "20250314",
        1, 10, 2, 5,
        3, 20, 4, 6,
        5, 30, 6, 7,
        7, 40, 8, 8,
        9, 99,
    )

    sectors = build_sectors_enhanced_payload("20250314", sectors_rows, top=10, filter_type="all")
    industries = build_industries_enhanced_payload("20250314", industries_rows, order="desc")
    ranking = build_ranking_enhanced_payload("20250314", ranking_rows, sort_by="pct_chg", order="desc", market="银行", industry=None)
    industry_stocks = build_industry_stocks_payload("20250314", "银行", "desc", stocks_rows)
    moneyflow = build_moneyflow_payload("000001.SZ", "20250314", moneyflow_row)

    assert sectors["sectors"][0]["sector"] == "科创板"
    assert industries["industries"][0]["name"] == "半导体"
    assert ranking["stocks"][0]["name"] == "000001"
    assert industry_stocks["up_count"] == 1
    assert moneyflow["small"]["net_amount"] == 5.0


def test_numeric_and_realtime_helpers_keep_existing_contracts():
    assert to_float(Decimal("1.23")) == 1.23
    assert build_connected_message("20250314")["type"] == "connected"
    assert build_status_message("20250314", 3)["connections"] == 3
    assert build_data_updated_message("20250314", previous_date="20250313", manual=True)["manual"] is True

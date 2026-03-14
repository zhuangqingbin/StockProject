from apps.stock_bi.codex.backend.modules.stock_detail.application import (
    build_aggregate_industry_kline_rows,
    build_company_info_payload,
    build_industry_base_payload,
    build_industry_stats_payload,
    build_stock_detail_payload,
    build_sw_industry_kline_rows,
    build_sw_industry_today_payload,
)


def test_build_stock_detail_payload_preserves_existing_shape():
    daily_row = ("000001.SZ", "20250314", 10, 11, 9, 10.5, 9.8, 2.1, 1000, 2000, "平安银行")
    basic_row = ("000001.SZ", "20250314", 3.2, 8.1, 8.0, 0.9, 100000, 80000, 1.5)
    kline_rows = [
        ("20250314", 10, 11, 9, 10.5, 1000, 2000, 2.1),
        ("20250313", 9, 10, 8.5, 9.8, 900, 1800, -0.1),
    ]
    company_row = ("000001.SZ", "平安银行", "深圳", "银行", "主板", "19910403")

    result = build_stock_detail_payload("000001.SZ", "20250314", daily_row, basic_row, kline_rows, company_row)

    assert result["trade_date"] == "2025-03-14"
    assert result["daily"]["name"] == "平安银行"
    assert result["basic"]["total_mv"] == 10.0
    assert result["kline"][0]["date"] == "2025-03-13"
    assert result["company"]["industry"] == "银行"


def test_build_company_info_payload_merges_optional_detail():
    base_row = ("000001.SZ", "000001", "平安银行", "深圳", "银行", "主板", "SZSE", "19910403")
    detail_row = ("董事长", "总经理", "董秘", 123456, "广东", "深圳", "介绍", "example.com", 1000, "主营")

    result = build_company_info_payload(base_row, detail_row)

    assert result["symbol"] == "000001"
    assert result["reg_capital"] == 123456.0
    assert result["main_business"] == "主营"


def test_build_industry_payload_helpers_cover_sw_and_aggregate_modes():
    base = build_industry_base_payload("半导体", "20250314")
    sw_kline = build_sw_industry_kline_rows([("20250314", 10, 11, 9, 10.5, 2000, 50000, 1.2)])
    sw_today = build_sw_industry_today_payload((10, 11, 9, 10.5, 1.2, 2000, 50000, 15, 2))
    agg_kline = build_aggregate_industry_kline_rows([("20250314", 10, 11, 9, 10.5, 200000, 500000000, 1.2)])
    stats = build_industry_stats_payload((20, 12, 6, 1.23, 88.8))

    assert base["trade_date"] == "2025-03-14"
    assert sw_kline[0]["amount"] == 5.0
    assert sw_today["pe"] == 15.0
    assert agg_kline[0]["vol"] == 20.0
    assert stats["stock_count"] == 20

from apps.stock_bi_v1.tests.support import create_test_client


def test_precompute_materializes_market_industry_and_limit_views(monkeypatch, tmp_path):
    client, SessionLocal = create_test_client(monkeypatch, tmp_path)

    from apps.stock_bi_v1.backend.models.db_models import (
        DailyBasic,
        DailyKline,
        IndexDaily,
        Moneyflow,
        MoneyflowHsgt,
        PrecomputedIndustry,
        PrecomputedLimit,
        PrecomputedMarket,
        StockBasic,
        StockStkLimit,
    )

    with SessionLocal() as session:
        session.add_all(
            [
                StockBasic(ts_code="000001.SZ", symbol="000001", name="平安银行", industry="银行", market="主板", exchange="SZSE"),
                StockBasic(ts_code="600000.SH", symbol="600000", name="浦发银行", industry="银行", market="主板", exchange="SSE"),
                StockBasic(ts_code="300750.SZ", symbol="300750", name="宁德时代", industry="电池", market="创业板", exchange="SZSE"),
                StockBasic(ts_code="002594.SZ", symbol="002594", name="比亚迪", industry="电池", market="主板", exchange="SZSE"),
                StockBasic(ts_code="600519.SH", symbol="600519", name="贵州茅台", industry="白酒", market="主板", exchange="SSE"),
            ]
        )
        session.add_all(
            [
                IndexDaily(ts_code="000001.SH", trade_date="20260313", close=3350.12, pct_chg=1.1, amount=120000000),
                IndexDaily(ts_code="399001.SZ", trade_date="20260313", close=10820.55, pct_chg=0.8, amount=98000000),
                IndexDaily(ts_code="399006.SZ", trade_date="20260313", close=2105.77, pct_chg=-0.2, amount=87000000),
                IndexDaily(ts_code="000688.SH", trade_date="20260313", close=901.31, pct_chg=1.6, amount=65000000),
                IndexDaily(ts_code="399005.SZ", trade_date="20260313", close=6888.88, pct_chg=0.5, amount=76000000),
            ]
        )
        session.add_all(
            [
                DailyKline(ts_code="000001.SZ", trade_date="20260311", open=10.0, high=11.0, low=9.8, close=11.0, pre_close=10.0, pct_chg=10.0, amount=900.0),
                DailyKline(ts_code="000001.SZ", trade_date="20260312", open=11.0, high=12.1, low=10.9, close=12.1, pre_close=11.0, pct_chg=10.0, amount=1100.0),
                DailyKline(ts_code="000001.SZ", trade_date="20260313", open=12.1, high=13.31, low=12.0, close=13.31, pre_close=12.1, pct_chg=10.0, amount=1500.0),
                DailyKline(ts_code="600000.SH", trade_date="20260313", open=10.8, high=11.88, low=10.6, close=11.20, pre_close=10.8, pct_chg=3.7, amount=2200.0),
                DailyKline(ts_code="300750.SZ", trade_date="20260313", open=200.0, high=202.0, low=198.0, close=200.0, pre_close=200.0, pct_chg=0.0, amount=5400.0),
                DailyKline(ts_code="002594.SZ", trade_date="20260313", open=300.0, high=301.0, low=292.0, close=292.5, pre_close=300.0, pct_chg=-2.5, amount=4100.0),
                DailyKline(ts_code="600519.SH", trade_date="20260313", open=1500.0, high=1505.0, low=1350.0, close=1350.0, pre_close=1500.0, pct_chg=-10.0, amount=1800.0),
            ]
        )
        session.add_all(
            [
                DailyBasic(ts_code="000001.SZ", trade_date="20260313", turnover_rate=12.5, pe_ttm=5.1, pb=0.6, ps_ttm=1.1, total_mv=250000.0),
                DailyBasic(ts_code="600000.SH", trade_date="20260313", turnover_rate=8.3, pe_ttm=4.9, pb=0.5, ps_ttm=1.0, total_mv=210000.0),
                DailyBasic(ts_code="300750.SZ", trade_date="20260313", turnover_rate=15.0, pe_ttm=20.0, pb=4.5, ps_ttm=3.2, total_mv=820000.0),
                DailyBasic(ts_code="002594.SZ", trade_date="20260313", turnover_rate=9.2, pe_ttm=18.0, pb=3.8, ps_ttm=2.5, total_mv=760000.0),
                DailyBasic(ts_code="600519.SH", trade_date="20260313", turnover_rate=2.0, pe_ttm=24.0, pb=8.0, ps_ttm=10.0, total_mv=2200000.0),
            ]
        )
        session.add_all(
            [
                Moneyflow(ts_code="000001.SZ", trade_date="20260313", net_mf_amount=300.0),
                Moneyflow(ts_code="600000.SH", trade_date="20260313", net_mf_amount=100.0),
                Moneyflow(ts_code="300750.SZ", trade_date="20260313", net_mf_amount=50.0),
                Moneyflow(ts_code="002594.SZ", trade_date="20260313", net_mf_amount=-30.0),
                Moneyflow(ts_code="600519.SH", trade_date="20260313", net_mf_amount=-200.0),
            ]
        )
        session.add(MoneyflowHsgt(trade_date="20260313", hgt=32.0, sgt=21.0, north_money=53.0, south_money=-12.0))
        session.add_all(
            [
                StockStkLimit(ts_code="000001.SZ", trade_date="20260311", pre_close=10.0, up_limit=11.0, down_limit=9.0),
                StockStkLimit(ts_code="000001.SZ", trade_date="20260312", pre_close=11.0, up_limit=12.1, down_limit=9.9),
                StockStkLimit(ts_code="000001.SZ", trade_date="20260313", pre_close=12.1, up_limit=13.31, down_limit=10.89),
                StockStkLimit(ts_code="600000.SH", trade_date="20260313", pre_close=10.8, up_limit=11.88, down_limit=9.72),
                StockStkLimit(ts_code="300750.SZ", trade_date="20260313", pre_close=200.0, up_limit=220.0, down_limit=180.0),
                StockStkLimit(ts_code="002594.SZ", trade_date="20260313", pre_close=300.0, up_limit=330.0, down_limit=270.0),
                StockStkLimit(ts_code="600519.SH", trade_date="20260313", pre_close=1500.0, up_limit=1650.0, down_limit=1350.0),
            ]
        )
        session.commit()

    response = client.post("/api/precompute/20260313")
    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "trade_date": "20260313"}

    with SessionLocal() as session:
        market_row = session.get(PrecomputedMarket, "20260313")
        limit_row = session.get(PrecomputedLimit, "20260313")
        industry_rows = session.query(PrecomputedIndustry).filter_by(trade_date="20260313").all()

    assert market_row is not None
    assert market_row.flat_count == 1
    assert market_row.up_limit_count == 1
    assert market_row.down_limit_count == 1
    assert market_row.total_amount == 15000.0
    assert market_row.distribution["0"] == 1
    assert market_row.top_gainers[0]["ts_code"] == "000001.SZ"
    assert market_row.top_turnover[0]["ts_code"] == "300750.SZ"

    assert len(industry_rows) == 3
    bank_row = next(row for row in industry_rows if row.industry == "银行")
    assert bank_row.avg_pct_chg == 6.85
    assert bank_row.net_mf_amount == 400.0

    assert limit_row is not None
    assert limit_row.up_count == 1
    assert limit_row.down_count == 1
    assert limit_row.broken_count == 1
    assert limit_row.broken_rate == 0.5
    assert limit_row.tier_stats == {"3": 1}
    assert limit_row.up_limit_stocks[0]["consecutive_days"] == 3
    assert limit_row.down_limit_stocks[0]["ts_code"] == "600519.SH"

    overview = client.get("/api/market/overview?date=20260313").json()
    assert overview["distribution"]["0"] == 1
    assert overview["top_amount"][0]["ts_code"] == "300750.SZ"
    assert overview["limit_stats"]["tier_stats"] == {"3": 1}

    heatmap = client.get("/api/industry/heatmap?date=20260313").json()
    assert heatmap[0]["industry"] == "银行"
    assert heatmap[0]["stock_count"] == 2

    limit_list = client.get("/api/market/limit-list?type=up&date=20260313").json()
    assert limit_list[0]["ts_code"] == "000001.SZ"
    assert limit_list[0]["consecutive_days"] == 3

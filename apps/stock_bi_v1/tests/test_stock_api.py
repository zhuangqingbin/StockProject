from apps.stock_bi_v1.tests.support import create_test_client


def test_stock_search_and_profile_routes(monkeypatch, tmp_path):
    client, SessionLocal = create_test_client(monkeypatch, tmp_path)

    from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, Moneyflow, StockBasic, TopList

    with SessionLocal() as session:
        session.add(StockBasic(ts_code="000001.SZ", symbol="000001", name="平安银行", industry="银行", market="主板", exchange="SZSE"))
        session.add_all(
            [
                DailyKline(
                    ts_code="000001.SZ",
                    trade_date="20260312",
                    open=11.2,
                    high=11.6,
                    low=11.0,
                    close=11.4,
                    pre_close=11.1,
                    change=0.3,
                    pct_chg=2.7,
                    vol=123456,
                    amount=4567890,
                ),
                DailyKline(
                    ts_code="000001.SZ",
                    trade_date="20260313",
                    open=11.5,
                    high=11.8,
                    low=11.3,
                    close=11.7,
                    pre_close=11.4,
                    change=0.3,
                    pct_chg=2.63,
                    vol=153456,
                    amount=5567890,
                ),
            ]
        )
        session.add_all(
            [
                DailyBasic(
                    ts_code="000001.SZ",
                    trade_date="20260313",
                    turnover_rate=1.8,
                    pe_ttm=6.2,
                    pb=0.7,
                    ps_ttm=1.1,
                    total_mv=210000000000,
                    circ_mv=180000000000,
                    total_share=19400000000,
                    float_share=16200000000,
                ),
                Moneyflow(
                    ts_code="000001.SZ",
                    trade_date="20260313",
                    buy_elg_amount=1000,
                    sell_elg_amount=400,
                    buy_lg_amount=900,
                    sell_lg_amount=300,
                    buy_md_amount=700,
                    sell_md_amount=200,
                    buy_sm_amount=600,
                    sell_sm_amount=250,
                    net_mf_amount=950,
                ),
                TopList(
                    ts_code="000001.SZ",
                    trade_date="20260313",
                    name="平安银行",
                    close=11.7,
                    pct_chg=2.63,
                    turnover_rate=1.8,
                    amount=5567890,
                    l_buy=2000000,
                    l_sell=1200000,
                    net_amount=800000,
                    reason="日涨幅偏离值达7%",
                ),
            ]
        )
        session.commit()

    search_response = client.get("/api/stock/search", params={"q": "平安"})
    assert search_response.status_code == 200
    assert search_response.json()[0]["ts_code"] == "000001.SZ"

    profile_response = client.get("/api/stock/000001.SZ/profile")
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["name"] == "平安银行"
    assert profile["current_price"] == 11.7
    assert profile["industry"] == "银行"

    kline_response = client.get("/api/stock/000001.SZ/kline", params={"period": "weekly"})
    assert kline_response.status_code == 200
    assert len(kline_response.json()) >= 1

    toplist_response = client.get("/api/toplist/stock/000001.SZ")
    assert toplist_response.status_code == 200
    assert toplist_response.json()[0]["reason"] == "日涨幅偏离值达7%"

from apps.stock_bi_v1.tests.support import create_test_client


def test_screener_supports_multi_condition_filters(monkeypatch, tmp_path):
    client, SessionLocal = create_test_client(monkeypatch, tmp_path)

    from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, Moneyflow, StockBasic

    with SessionLocal() as session:
        session.add_all(
            [
                StockBasic(ts_code="000001.SZ", symbol="000001", name="平安银行", industry="银行", market="主板", exchange="SZSE"),
                StockBasic(ts_code="600000.SH", symbol="600000", name="浦发银行", industry="银行", market="主板", exchange="SSE"),
                StockBasic(ts_code="000004.SZ", symbol="000004", name="ST国华", industry="银行", market="主板", exchange="SZSE"),
            ]
        )
        session.add_all(
            [
                DailyKline(ts_code="000001.SZ", trade_date="20260313", close=11.7, pct_chg=2.63, amount=5567890, vol=153456),
                DailyKline(ts_code="600000.SH", trade_date="20260313", close=9.8, pct_chg=0.52, amount=2567890, vol=95321),
                DailyKline(ts_code="000004.SZ", trade_date="20260313", close=5.6, pct_chg=3.52, amount=1567890, vol=75321),
            ]
        )
        session.add_all(
            [
                DailyBasic(ts_code="000001.SZ", trade_date="20260313", turnover_rate=1.8, pe_ttm=6.2, pb=0.7, ps_ttm=1.1, total_mv=210000000000, circ_mv=180000000000),
                DailyBasic(ts_code="600000.SH", trade_date="20260313", turnover_rate=0.9, pe_ttm=8.5, pb=0.6, ps_ttm=1.0, total_mv=150000000000, circ_mv=120000000000),
                DailyBasic(ts_code="000004.SZ", trade_date="20260313", turnover_rate=3.2, pe_ttm=4.5, pb=0.4, ps_ttm=0.8, total_mv=50000000000, circ_mv=42000000000),
            ]
        )
        session.add_all(
            [
                Moneyflow(ts_code="000001.SZ", trade_date="20260313", buy_elg_amount=1000, sell_elg_amount=400, buy_lg_amount=900, sell_lg_amount=300, buy_md_amount=700, sell_md_amount=200, buy_sm_amount=600, sell_sm_amount=250, net_mf_amount=950),
                Moneyflow(ts_code="600000.SH", trade_date="20260313", buy_elg_amount=500, sell_elg_amount=300, buy_lg_amount=400, sell_lg_amount=200, buy_md_amount=300, sell_md_amount=150, buy_sm_amount=200, sell_sm_amount=180, net_mf_amount=320),
                Moneyflow(ts_code="000004.SZ", trade_date="20260313", buy_elg_amount=800, sell_elg_amount=100, buy_lg_amount=700, sell_lg_amount=200, buy_md_amount=400, sell_md_amount=150, buy_sm_amount=320, sell_sm_amount=120, net_mf_amount=1200),
            ]
        )
        session.commit()

    filters_response = client.get("/api/screener/filters")
    assert filters_response.status_code == 200
    assert any(item["field"] == "pct_chg" for item in filters_response.json())

    query_response = client.post(
        "/api/screener/query",
        json={
            "conditions": [
                {"field": "pct_chg", "operator": "gt", "value": 1},
                {"field": "pe_ttm", "operator": "lt", "value": 7},
                {"field": "industry", "operator": "eq", "value": "银行"},
            ],
            "sort_by": "pct_chg",
            "order": "desc",
            "page": 0,
            "size": 20,
        },
    )
    assert query_response.status_code == 200
    payload = query_response.json()

    assert payload["total"] == 1
    assert payload["items"][0]["ts_code"] == "000001.SZ"
    assert all(not item["name"].startswith("ST") for item in payload["items"])

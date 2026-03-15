from apps.stock_bi_v1.tests.support import create_test_client


def test_market_overview_returns_dashboard_contract(monkeypatch, tmp_path):
    client, SessionLocal = create_test_client(monkeypatch, tmp_path)

    from apps.stock_bi_v1.backend.models.db_models import (
        IndexDaily,
        PrecomputedLimit,
        PrecomputedMarket,
        StockBasic,
    )

    with SessionLocal() as session:
        session.add_all(
            [
                StockBasic(ts_code="000001.SZ", symbol="000001", name="平安银行", industry="银行", market="主板", exchange="SZSE"),
                StockBasic(ts_code="600000.SH", symbol="600000", name="浦发银行", industry="银行", market="主板", exchange="SSE"),
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
        session.add(
            PrecomputedMarket(
                trade_date="20260313",
                distribution={"-3~0": 1200, "0~3": 1800},
                up_limit_count=12,
                down_limit_count=1,
                flat_count=123,
                total_amount=3456789000,
                top_gainers=[
                    {"ts_code": "000001.SZ", "name": "平安银行", "pct_chg": 5.21, "close": 12.31},
                    {"ts_code": "600000.SH", "name": "浦发银行", "pct_chg": 3.12, "close": 10.88},
                ],
                top_losers=[],
                top_amount=[],
                top_turnover=[],
            )
        )
        session.add(
            PrecomputedLimit(
                trade_date="20260313",
                up_limit_stocks=[{"ts_code": "000001.SZ", "name": "平安银行", "industry": "银行"}],
                down_limit_stocks=[],
                up_count=12,
                down_count=1,
                broken_count=3,
                broken_rate=0.2,
                tier_stats={"1": 8, "2": 3, "3": 1},
            )
        )
        session.commit()

    overview_response = client.get("/api/market/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()

    assert overview["trade_date"] == "20260313"
    assert len(overview["indices"]) == 5
    assert overview["top_gainers"][0]["ts_code"] == "000001.SZ"
    assert overview["limit_stats"]["up_count"] == 12

    indices_response = client.get("/api/market/indices")
    assert indices_response.status_code == 200
    assert indices_response.json()[0]["name"]

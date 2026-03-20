from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from apps.data_hub.data_pipeline_ts.execution.calendar import get_trade_cal
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_income_vip import IncomeVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.client import ClientConfig, TuShareClient


class _FakeClock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = now
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_tushare_client_retries_and_returns_frame(tmp_path) -> None:
    pro = MagicMock()
    pro.daily.side_effect = [RuntimeError("boom"), pd.DataFrame({"ts_code": ["000001.SZ"]})]

    client = TuShareClient(
        config=ClientConfig(
            retries=1,
            backoff_seconds=0.0,
            cache_dir=str(tmp_path),
            min_interval_seconds=0.0,
        ),
        pro=pro,
    )

    result = client.call("daily", trade_date="20260317")

    assert list(result["ts_code"]) == ["000001.SZ"]
    assert pro.daily.call_count == 2


def test_tushare_client_pro_bar_retries_and_returns_frame(tmp_path, monkeypatch) -> None:
    pro = MagicMock()
    pro_bar = MagicMock(side_effect=[RuntimeError("boom"), pd.DataFrame({"ts_code": ["000001.SZ"]})])
    monkeypatch.setattr("apps.data_hub.data_pipeline_ts.fetchers.client.ts", MagicMock(pro_bar=pro_bar))

    client = TuShareClient(
        config=ClientConfig(
            retries=1,
            backoff_seconds=0.0,
            cache_dir=str(tmp_path),
            min_interval_seconds=0.0,
        ),
        pro=pro,
    )

    result = client.pro_bar(ts_code="000001.SZ", asset="E", adj="qfq", freq="D", start_date="20260318", end_date="20260318")

    assert list(result["ts_code"]) == ["000001.SZ"]
    assert pro_bar.call_count == 2
    assert pro_bar.call_args.kwargs == {
        "ts_code": "000001.SZ",
        "asset": "E",
        "adj": "qfq",
        "freq": "D",
        "start_date": "20260318",
        "end_date": "20260318",
    }


def test_tushare_client_respects_max_calls_per_minute(tmp_path, monkeypatch) -> None:
    pro = MagicMock()
    pro.daily.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ"]}),
        pd.DataFrame({"ts_code": ["000002.SZ"]}),
    ]
    clock = _FakeClock(now=100.0)
    monkeypatch.setattr("apps.data_hub.data_pipeline_ts.fetchers.client.time.monotonic", clock.monotonic)
    monkeypatch.setattr("apps.data_hub.data_pipeline_ts.fetchers.client.time.time", clock.time)
    monkeypatch.setattr("apps.data_hub.data_pipeline_ts.fetchers.client.time.sleep", clock.sleep)

    client = TuShareClient(
        config=ClientConfig(
            retries=0,
            backoff_seconds=0.0,
            cache_dir=str(tmp_path),
            min_interval_seconds=0.0,
            max_calls_per_minute=1,
        ),
        pro=pro,
    )

    client.call("daily", trade_date="20260317")
    client.call("daily", trade_date="20260318")

    assert clock.sleeps == [60.0]
    assert pro.daily.call_count == 2


def test_get_trade_cal_uses_fetcher_and_filters_open_days() -> None:
    fetcher = MagicMock()
    fetcher.fetch.return_value = pd.DataFrame(
        {
            "cal_date": ["20260316", "20260317"],
            "is_open": [0, 1],
        }
    )

    assert get_trade_cal("20260316", "20260317", fetcher_cls=lambda: fetcher) == ["20260317"]
    fetcher.fetch.assert_called_once_with(start_date="20260316", end_date="20260317")


def test_income_vip_passes_ann_date_through_directly() -> None:
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260317"],
            "end_date": ["20251231"],
            "basic_eps": [1.0],
            "total_revenue": [2.0],
            "revenue": [3.0],
            "operate_profit": [4.0],
            "total_profit": [5.0],
            "n_income": [6.0],
            "n_income_attr_p": [7.0],
            "sell_exp": [8.0],
            "admin_exp": [9.0],
            "fin_exp": [10.0],
            "rd_exp": [11.0],
        }
    )

    fetcher = IncomeVipFetch(client=client)
    fetcher.fetch(ann_date="20260317")

    client.call.assert_called_once_with(
        "income_vip",
        ann_date="20260317",
        fields=",".join(fetcher.fields),
    )

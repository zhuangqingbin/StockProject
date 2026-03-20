from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from apps.data_hub.data_pipeline_ak.calendar import get_prev_trade_days


def test_get_prev_trade_days_uses_akshare_trade_calendar() -> None:
    fake_akshare = MagicMock()
    fake_akshare.tool_trade_date_hist_sina.return_value = pd.DataFrame(
        {"trade_date": ["2026-03-13", "2026-03-16", "2026-03-17"]}
    )

    assert get_prev_trade_days("2026-03-17", 2, akshare_client=fake_akshare) == [
        "2026-03-13",
        "2026-03-16",
    ]

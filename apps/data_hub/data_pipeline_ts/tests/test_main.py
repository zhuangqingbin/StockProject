from __future__ import annotations

from apps.data_hub.data_pipeline_ts.main import build_parser


def test_build_parser_supports_modes_and_filters():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--mode",
            "backfill",
            "--profiles",
            "trade_day_pre_open,financial_calendar_nightly",
            "--jobs",
            "stock_daily,stock_daily_basic",
            "--start",
            "20260101",
            "--end",
            "20260317",
            "--max-workers",
            "4",
        ]
    )

    assert args.mode == "backfill"
    assert args.profiles == "trade_day_pre_open,financial_calendar_nightly"
    assert args.jobs == "stock_daily,stock_daily_basic"
    assert args.start == "20260101"
    assert args.end == "20260317"
    assert args.max_workers == 4

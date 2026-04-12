from __future__ import annotations

from apps.data_hub.data_pipeline_ts import main as main_module
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


def test_main_invokes_quant_research_post_hook(monkeypatch):
    captured = {}

    def fake_run_once(**kwargs):
        captured["run_once"] = kwargs
        return ["result"]

    def fake_post_hook(**kwargs):
        captured["post_hook"] = kwargs
        return []

    monkeypatch.setattr(main_module, "run_once", fake_run_once)
    monkeypatch.setattr(main_module, "maybe_run_quant_research_publish", fake_post_hook)

    exit_code = main_module.main(["--profiles", "reference_calendar_nightly", "--as-of", "2026-04-04"])

    assert exit_code == 0
    assert captured["run_once"]["profiles"] == ["reference_calendar_nightly"]
    assert captured["run_once"]["writer"] is not None
    assert captured["post_hook"]["mode"] == "once"
    assert captured["post_hook"]["profiles"] == ["reference_calendar_nightly"]
    assert captured["post_hook"]["job_names"] is None
    assert captured["post_hook"]["results"] == ["result"]
    assert captured["post_hook"]["as_of"] == "2026-04-04"
    assert captured["post_hook"]["writer"] is captured["run_once"]["writer"]


def test_main_keeps_zero_exit_code_when_quant_research_post_hook_fails(monkeypatch):
    class HookResult:
        status = "failed"

    monkeypatch.setattr(main_module, "run_once", lambda **kwargs: ["result"])
    monkeypatch.setattr(main_module, "maybe_run_quant_research_publish", lambda **kwargs: [HookResult()])

    exit_code = main_module.main(["--profiles", "reference_calendar_nightly"])

    assert exit_code == 0

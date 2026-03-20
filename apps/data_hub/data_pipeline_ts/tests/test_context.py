from __future__ import annotations

from datetime import date

from apps.data_hub.data_pipeline_ts.execution.context import ExecutionContext


def test_execution_context_uses_latest_trade_date():
    calls: list[tuple[str, str]] = []

    def fake_trade_calendar(start_date: str, end_date: str) -> list[str]:
        calls.append((start_date, end_date))
        return ["20260312", "20260313"]

    context = ExecutionContext.for_as_of("2026-03-14", trade_calendar_provider=fake_trade_calendar)

    assert context.as_of_date == date(2026, 3, 14)
    assert context.trade_date == date(2026, 3, 13)
    assert context.variables() == {
        "current_dt": "2026-03-14",
        "current_date": "20260314",
        "trade_dt": "2026-03-13",
        "trade_date": "20260313",
    }
    assert context.render_mapping(
        {
            "trade_date": "{{ trade_date }}",
            "window_end": "{{ current_date }}",
        }
    ) == {
        "trade_date": "20260313",
        "window_end": "20260314",
    }
    assert calls


def test_execution_context_handles_descending_trade_calendar():
    def fake_trade_calendar(start_date: str, end_date: str) -> list[str]:
        return ["20260206", "20260205", "20260204", "20260126"]

    context = ExecutionContext.for_as_of("2026-02-09", trade_calendar_provider=fake_trade_calendar)

    assert context.trade_date == date(2026, 2, 6)

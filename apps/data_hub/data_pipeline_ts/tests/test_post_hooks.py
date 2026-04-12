from __future__ import annotations

from apps.data_hub.data_pipeline_ts.execution.post_hooks import maybe_run_quant_research_publish
from apps.data_hub.data_pipeline_ts.jobs.specs import JobRunResult


def _result(*, profile: str, status: str = "success") -> JobRunResult:
    return JobRunResult(
        job_name=f"{profile}_job",
        table_name="demo",
        params={},
        rows_fetched=1,
        rows_written=1,
        duration_seconds=0.1,
        status=status,
        trigger_profile=profile,
        run_mode="once",
        as_of_date="20260404",
        effective_date="20260404",
    )


def test_post_hook_runs_quant_research_publish_when_reference_calendar_profile_succeeds(monkeypatch):
    monkeypatch.setenv("QV_RESEARCH_AUTO_PUBLISH_ENABLED", "1")
    monkeypatch.setenv("QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION", "1")
    captured = {}

    def fake_publish(params):
        captured["params"] = params
        return {"factor_count": 12}

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.post_hooks._run_quant_research_publish",
        fake_publish,
    )

    results = maybe_run_quant_research_publish(
        mode="once",
        profiles=["reference_calendar_nightly"],
        job_names=None,
        results=[_result(profile="reference_calendar_nightly")],
        as_of="2026-04-04",
    )

    assert len(results) == 1
    assert results[0].job_name == "quant_research_publish"
    assert results[0].status == "success"
    assert results[0].rows_written == 12
    assert captured["params"]["end_date"] == "2026-04-04"
    assert captured["params"]["include_chip_distribution"] is False


def test_post_hook_skips_when_reference_profile_failed(monkeypatch):
    monkeypatch.setenv("QV_RESEARCH_AUTO_PUBLISH_ENABLED", "1")
    called = {"value": False}

    def fake_publish(params):
        called["value"] = True
        return {"factor_count": 12}

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.post_hooks._run_quant_research_publish",
        fake_publish,
    )

    results = maybe_run_quant_research_publish(
        mode="once",
        profiles=["reference_calendar_nightly"],
        job_names=None,
        results=[_result(profile="reference_calendar_nightly", status="failed")],
        as_of="2026-04-04",
    )

    assert results == []
    assert called["value"] is False


def test_post_hook_skips_for_non_trigger_profile(monkeypatch):
    monkeypatch.setenv("QV_RESEARCH_AUTO_PUBLISH_ENABLED", "1")
    called = {"value": False}

    def fake_publish(params):
        called["value"] = True
        return {"factor_count": 12}

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.post_hooks._run_quant_research_publish",
        fake_publish,
    )

    results = maybe_run_quant_research_publish(
        mode="once",
        profiles=["trade_day_post_close_extended"],
        job_names=None,
        results=[_result(profile="trade_day_post_close_extended")],
        as_of="2026-04-04",
    )

    assert results == []
    assert called["value"] is False


def test_post_hook_skips_when_job_filter_is_present(monkeypatch):
    monkeypatch.setenv("QV_RESEARCH_AUTO_PUBLISH_ENABLED", "1")
    called = {"value": False}

    def fake_publish(params):
        called["value"] = True
        return {"factor_count": 12}

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.post_hooks._run_quant_research_publish",
        fake_publish,
    )

    results = maybe_run_quant_research_publish(
        mode="once",
        profiles=["reference_calendar_nightly"],
        job_names=["trade_cal"],
        results=[_result(profile="reference_calendar_nightly")],
        as_of="2026-04-04",
    )

    assert results == []
    assert called["value"] is False

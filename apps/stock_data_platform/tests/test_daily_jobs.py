from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine

from apps.stock_data_platform.DataFetch.FetchIndex import BI_TRACKED_INDEX_CODES, IndexDailyFetch
from apps.stock_data_platform.jobs import runtime


def test_execution_context_uses_latest_trade_date():
    calls: list[tuple[str, str]] = []

    def fake_trade_calendar(start_date: str, end_date: str) -> list[str]:
        calls.append((start_date, end_date))
        return ["20260312", "20260313"]

    context = runtime.ExecutionContext.for_as_of("2026-03-14", trade_calendar_provider=fake_trade_calendar)

    assert context.as_of_date == date(2026, 3, 14)
    assert context.trade_date == date(2026, 3, 13)
    assert context.render_mapping(
        {
            "trade_date": "{{ trade_date_compact }}",
            "window_end": "{{ as_of_date_compact }}",
        }
    ) == {
        "trade_date": "20260313",
        "window_end": "20260314",
    }
    assert calls


def test_execution_context_handles_descending_trade_calendar():
    def fake_trade_calendar(start_date: str, end_date: str) -> list[str]:
        return ["20260206", "20260205", "20260204", "20260126"]

    context = runtime.ExecutionContext.for_as_of("2026-02-09", trade_calendar_provider=fake_trade_calendar)

    assert context.trade_date == date(2026, 2, 6)


def test_load_job_definitions_resolves_fetcher_names_and_scope_columns(tmp_path, monkeypatch):
    config_path = tmp_path / "daily_jobs.yaml"
    config_path.write_text(
        "\n".join(
            [
                "jobs:",
                "  - name: fake_daily",
                "    fetcher: FakeFetcher",
                "    table_name: fake_daily_table",
                "    params:",
                "      trade_date: '{{ trade_date_compact }}'",
                "    scope_columns:",
                "      - trade_date",
            ]
        ),
        encoding="utf-8",
    )

    class FakeFetcher:
        pass

    monkeypatch.setattr(runtime, "_resolve_fetcher_class", lambda name: FakeFetcher)

    jobs = runtime.load_job_definitions(config_path)

    assert len(jobs) == 1
    assert jobs[0].name == "fake_daily"
    assert jobs[0].fetcher_cls is FakeFetcher
    assert jobs[0].table_name == "fake_daily_table"
    assert jobs[0].params == {"trade_date": "{{ trade_date_compact }}"}
    assert jobs[0].scope_columns == ("trade_date",)
    assert jobs[0].trigger_stock_bi_sync is False


def test_load_job_definitions_defaults_stock_bi_sync_for_mirrored_jobs(tmp_path, monkeypatch):
    config_path = tmp_path / "daily_jobs.yaml"
    config_path.write_text(
        "\n".join(
            [
                "jobs:",
                "  - name: fake_daily",
                "    fetcher: FakeFetcher",
                "    table_name: fake_daily_table",
                "    mirror_table_names:",
                "      - bi_fake_table",
                "    params:",
                "      trade_date: '{{ trade_date_compact }}'",
            ]
        ),
        encoding="utf-8",
    )

    class FakeFetcher:
        pass

    monkeypatch.setattr(runtime, "_resolve_fetcher_class", lambda name: FakeFetcher)

    jobs = runtime.load_job_definitions(config_path)

    assert jobs[0].trigger_stock_bi_sync is True


def test_run_jobs_renders_templates_and_calls_writer():
    state: dict[str, object] = {}

    class FakeFetcher:
        def fetch(self, **kwargs):
            state["kwargs"] = kwargs
            return pd.DataFrame(
                [
                    {
                        "trade_date": "20260313",
                        "ts_code": "000001.SZ",
                        "close": 12.3,
                    }
                ]
            )

    class FakeWriter:
        def write(self, job_definition, frame):
            state["job_name"] = job_definition.name
            state["rows"] = frame.to_dict("records")
            return len(frame.index)

    context = runtime.ExecutionContext(
        as_of_date=date(2026, 3, 14),
        trade_date=date(2026, 3, 13),
    )
    jobs = [
        runtime.JobDefinition(
            name="stock_daily",
            fetcher_cls=FakeFetcher,
            table_name="stock_daily",
            params={"trade_date": "{{ trade_date_compact }}"},
            scope_columns=("trade_date",),
        )
    ]

    results = runtime.run_jobs(jobs, context=context, writer=FakeWriter())

    assert state["kwargs"] == {"trade_date": "20260313"}
    assert state["job_name"] == "stock_daily"
    assert results[0].job_name == "stock_daily"
    assert results[0].rows_fetched == 1
    assert results[0].rows_written == 1


def test_run_jobs_reports_job_context_when_fetch_fails():
    class ExplodingFetcher:
        def fetch(self, **kwargs):
            raise RuntimeError("upstream boom")

    context = runtime.ExecutionContext(
        as_of_date=date(2026, 2, 10),
        trade_date=date(2026, 2, 9),
    )
    jobs = [
        runtime.JobDefinition(
            name="index_daily",
            fetcher_cls=ExplodingFetcher,
            table_name="stock_index_daily",
            mirror_table_names=("index_daily",),
            params={"trade_date": "{{ trade_date_compact }}"},
            scope_columns=("trade_date",),
        )
    ]

    with pytest.raises(RuntimeError) as exc_info:
        runtime.run_jobs(jobs, context=context)

    message = str(exc_info.value)
    assert "job=index_daily" in message
    assert "primary_table=stock_index_daily" in message
    assert "target_tables=stock_index_daily,index_daily" in message
    assert "trade_date=20260209" in message


def test_database_writer_replaces_existing_scope_rows():
    engine = create_engine("sqlite://")
    existing = pd.DataFrame(
        [
            {"trade_date": "20260312", "ts_code": "000001.SZ", "close": 10.0},
            {"trade_date": "20260313", "ts_code": "000001.SZ", "close": 11.0},
        ]
    )
    existing.to_sql("stock_daily", con=engine, if_exists="replace", index=False)

    writer = runtime.DatabaseWriter(engine=engine)
    job = runtime.JobDefinition(
        name="stock_daily",
        fetcher_cls=object,
        table_name="stock_daily",
        params={"trade_date": "{{ trade_date_compact }}"},
        scope_columns=("trade_date",),
    )
    incoming = pd.DataFrame(
        [
            {"trade_date": "20260313", "ts_code": "000002.SZ", "close": 12.0},
        ]
    )

    rows_written = writer.write(job, incoming)
    stored = pd.read_sql_table("stock_daily", con=engine).sort_values(
        ["trade_date", "ts_code"]
    )
    records = stored.to_dict("records")

    assert rows_written == 1
    assert records == [
        {"trade_date": "20260312", "ts_code": "000001.SZ", "close": 10.0},
        {"trade_date": "20260313", "ts_code": "000002.SZ", "close": 12.0},
    ]


def test_database_writer_mirrors_rows_to_legacy_tables():
    engine = create_engine("sqlite://")
    writer = runtime.DatabaseWriter(engine=engine)
    job = runtime.JobDefinition(
        name="stock_daily",
        fetcher_cls=object,
        table_name="stock_daily",
        mirror_table_names=("daily_kline",),
        params={"trade_date": "{{ trade_date_compact }}"},
        scope_columns=("trade_date",),
    )
    incoming = pd.DataFrame(
        [
            {"trade_date": "20260313", "ts_code": "000002.SZ", "close": 12.0},
        ]
    )

    rows_written = writer.write(job, incoming)
    primary_records = pd.read_sql_table("stock_daily", con=engine).to_dict("records")
    mirror_records = pd.read_sql_table("daily_kline", con=engine).to_dict("records")

    assert rows_written == 1
    assert primary_records == mirror_records == [
        {"trade_date": "20260313", "ts_code": "000002.SZ", "close": 12.0},
    ]


def test_index_daily_fetch_with_trade_date_queries_curated_index_codes():
    calls: list[dict[str, str]] = []

    class FakeClient:
        pro = object()

        def call(self, endpoint: str, **kwargs):
            calls.append({"endpoint": endpoint, **kwargs})
            return pd.DataFrame(
                [
                    {
                        "ts_code": kwargs["ts_code"],
                        "trade_date": kwargs["trade_date"],
                        "close": 1.0,
                    }
                ]
            )

    fetcher = IndexDailyFetch(client=FakeClient())

    frame = fetcher.read_data(trade_date="20260209")

    assert [call["ts_code"] for call in calls] == list(BI_TRACKED_INDEX_CODES)
    assert all(call["endpoint"] == "index_daily" for call in calls)
    assert all(call["trade_date"] == "20260209" for call in calls)
    assert frame["ts_code"].tolist() == list(BI_TRACKED_INDEX_CODES)


def test_daily_runner_main_executes_requested_jobs(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    observed_calls: list[list[str]] = []

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        observed_calls.append(list(job_names or []))
        return [
            runtime.JobRunResult(
                job_name=(job_names or ["stock_daily"])[0],
                table_name=(job_names or ["stock_daily"])[0],
                written_tables=((job_names or ["stock_daily"])[0],),
                params={"trade_date": "20260313"},
                rows_fetched=123,
                rows_written=123,
            )
        ]

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)

    exit_code = daily_runner.main(["--jobs", "stock_daily,money_flow", "--as-of", "2026-03-14"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert observed_calls == [["stock_daily"], ["money_flow"]]
    assert "stock_daily" in stdout
    assert "money_flow" in stdout


def test_daily_runner_retries_only_failed_jobs_after_delay(monkeypatch):
    from apps.stock_data_platform.jobs import daily_runner

    calls: list[list[str]] = []
    sleep_calls: list[int] = []
    attempts = {"index_daily": 0}

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        requested_job_names = list(job_names or [])
        calls.append(requested_job_names)

        if requested_job_names == ["stock_daily"]:
            return [
                runtime.JobRunResult(
                    job_name="stock_daily",
                    table_name="stock_daily",
                    written_tables=("stock_daily", "daily_kline"),
                    trigger_stock_bi_sync=True,
                    params={"trade_date": "20260313"},
                    rows_fetched=100,
                    rows_written=100,
                )
            ]

        if requested_job_names == ["index_daily"]:
            attempts["index_daily"] += 1
            if attempts["index_daily"] == 1:
                raise RuntimeError(
                    "Daily job failed: job=index_daily, primary_table=stock_index_daily, "
                    "target_tables=stock_index_daily,index_daily, trade_date=20260313"
                )
            return [
                runtime.JobRunResult(
                    job_name="index_daily",
                    table_name="stock_index_daily",
                    written_tables=("stock_index_daily", "index_daily"),
                    trigger_stock_bi_sync=True,
                    params={"trade_date": "20260313"},
                    rows_fetched=5,
                    rows_written=5,
                )
            ]

        raise AssertionError(f"Unexpected job_names={requested_job_names}")

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)

    results = daily_runner.run_configured_jobs_until_success(
        as_of="2026-03-14",
        job_names=["stock_daily", "index_daily"],
        retry_delay_sec=600,
        sleep_fn=sleep_calls.append,
    )

    assert [result.job_name for result in results] == ["stock_daily", "index_daily"]
    assert calls == [["stock_daily"], ["index_daily"], ["index_daily"]]
    assert sleep_calls == [600]


def test_daily_runner_main_defers_stock_bi_sync_until_retries_finish(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    events: list[str] = []
    attempts = {"stock_daily": 0}

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        requested_job_names = list(job_names or [])
        events.append(f"run:{requested_job_names[0]}")

        if requested_job_names != ["stock_daily"]:
            raise AssertionError(f"Unexpected job_names={requested_job_names}")

        attempts["stock_daily"] += 1
        if attempts["stock_daily"] == 1:
            raise RuntimeError(
                "Daily job failed: job=stock_daily, primary_table=stock_daily, "
                "target_tables=stock_daily,daily_kline, trade_date=20260313"
            )

        return [
            runtime.JobRunResult(
                job_name="stock_daily",
                table_name="stock_daily",
                written_tables=("stock_daily", "daily_kline"),
                trigger_stock_bi_sync=True,
                params={"trade_date": "20260313"},
                rows_fetched=123,
                rows_written=123,
            )
        ]

    def fake_sleep(delay_sec: int):
        events.append(f"sleep:{delay_sec}")

    def fake_sync_stock_bi(trade_date: str):
        events.append(f"sync:{trade_date}")
        return {"status": "ok", "trade_date": trade_date}

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)
    monkeypatch.setattr(daily_runner.time, "sleep", fake_sleep)
    monkeypatch.setattr(daily_runner, "sync_stock_bi", fake_sync_stock_bi)

    exit_code = daily_runner.main(["--jobs", "stock_daily", "--as-of", "2026-03-14"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert events == ["run:stock_daily", "sleep:600", "run:stock_daily", "sync:20260313"]
    assert "Retrying failed jobs after 600 seconds" in stdout


def test_daily_runner_main_triggers_stock_bi_sync(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    observed: dict[str, object] = {}

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        return [
            runtime.JobRunResult(
                job_name="stock_daily",
                table_name="stock_daily",
                written_tables=("stock_daily", "daily_kline"),
                trigger_stock_bi_sync=True,
                params={"trade_date": "20260313"},
                rows_fetched=123,
                rows_written=123,
            )
        ]

    def fake_sync_stock_bi(trade_date: str):
        observed["trade_date"] = trade_date
        return {"status": "ok", "trade_date": trade_date}

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)
    monkeypatch.setattr(daily_runner, "sync_stock_bi", fake_sync_stock_bi)

    exit_code = daily_runner.main(["--jobs", "stock_daily", "--as-of", "2026-03-14"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert observed["trade_date"] == "20260313"
    assert "stock_bi sync" in stdout


def test_daily_runner_main_triggers_stock_bi_sync_for_new_bi_table(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    observed: dict[str, object] = {}
    monkeypatch.setattr(
        daily_runner,
        "load_job_definitions",
        lambda config_path=None: [
            runtime.JobDefinition(
                name="custom_feature",
                fetcher_cls=object,
                table_name="stock_custom_feature",
                mirror_table_names=("bi_custom_feature",),
                params={"trade_date": "{{ trade_date_compact }}"},
                trigger_stock_bi_sync=True,
            )
        ],
    )

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        return [
            runtime.JobRunResult(
                job_name="custom_feature",
                table_name="stock_custom_feature",
                written_tables=("stock_custom_feature", "bi_custom_feature"),
                trigger_stock_bi_sync=True,
                params={"trade_date": "20260313"},
                rows_fetched=5,
                rows_written=5,
            )
        ]

    def fake_sync_stock_bi(trade_date: str):
        observed["trade_date"] = trade_date
        return {"status": "ok", "trade_date": trade_date}

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)
    monkeypatch.setattr(daily_runner, "sync_stock_bi", fake_sync_stock_bi)

    exit_code = daily_runner.main(["--jobs", "custom_feature", "--as-of", "2026-03-14"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert observed["trade_date"] == "20260313"
    assert "custom_feature" in stdout


def test_daily_runner_main_triggers_stock_bi_v1_precompute_after_full_run(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    events: list[str] = []
    monkeypatch.setattr(
        daily_runner,
        "load_job_definitions",
        lambda config_path=None: [
            runtime.JobDefinition(
                name="stock_daily",
                fetcher_cls=object,
                table_name="stock_daily",
                mirror_table_names=("daily_kline",),
                params={"trade_date": "{{ trade_date_compact }}"},
                trigger_stock_bi_sync=True,
            ),
            runtime.JobDefinition(
                name="stk_limit",
                fetcher_cls=object,
                table_name="stock_stk_limit",
                params={"trade_date": "{{ trade_date_compact }}"},
                trigger_stock_bi_sync=False,
            ),
        ],
    )

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        requested_job_name = list(job_names or [])[0]
        events.append(f"run:{requested_job_name}")
        if requested_job_name == "stock_daily":
            return [
                runtime.JobRunResult(
                    job_name="stock_daily",
                    table_name="stock_daily",
                    written_tables=("stock_daily", "daily_kline"),
                    trigger_stock_bi_sync=True,
                    params={"trade_date": "20260313"},
                    rows_fetched=123,
                    rows_written=123,
                )
            ]
        if requested_job_name == "stk_limit":
            return [
                runtime.JobRunResult(
                    job_name="stk_limit",
                    table_name="stock_stk_limit",
                    written_tables=("stock_stk_limit",),
                    trigger_stock_bi_sync=False,
                    params={"trade_date": "20260313"},
                    rows_fetched=123,
                    rows_written=123,
                )
            ]
        raise AssertionError(f"Unexpected job_names={job_names}")

    def fake_sync_stock_bi(trade_date: str):
        events.append(f"stock_bi:{trade_date}")
        return {"status": "ok", "trade_date": trade_date}

    def fake_trigger_stock_bi_v1_precompute(trade_date: str):
        events.append(f"stock_bi_v1:{trade_date}")
        return {"status": "accepted", "trade_date": trade_date}

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)
    monkeypatch.setattr(daily_runner, "sync_stock_bi", fake_sync_stock_bi)
    monkeypatch.setattr(daily_runner, "trigger_stock_bi_v1_precompute", fake_trigger_stock_bi_v1_precompute)

    exit_code = daily_runner.main(["--as-of", "2026-03-14"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert events == ["run:stock_daily", "run:stk_limit", "stock_bi:20260313", "stock_bi_v1:20260313"]
    assert "stock_bi_v1 precompute" in stdout


def test_daily_runner_main_skips_stock_bi_v1_precompute_for_partial_run(monkeypatch, capsys):
    from apps.stock_data_platform.jobs import daily_runner

    events: list[str] = []
    monkeypatch.setattr(
        daily_runner,
        "load_job_definitions",
        lambda config_path=None: [
            runtime.JobDefinition(
                name="stock_daily",
                fetcher_cls=object,
                table_name="stock_daily",
                mirror_table_names=("daily_kline",),
                params={"trade_date": "{{ trade_date_compact }}"},
                trigger_stock_bi_sync=True,
            ),
            runtime.JobDefinition(
                name="stk_limit",
                fetcher_cls=object,
                table_name="stock_stk_limit",
                params={"trade_date": "{{ trade_date_compact }}"},
                trigger_stock_bi_sync=False,
            ),
        ],
    )

    def fake_run_configured_jobs(config_path=None, as_of=None, job_names=None, writer=None):
        requested_job_name = list(job_names or [])[0]
        events.append(f"run:{requested_job_name}")
        return [
            runtime.JobRunResult(
                job_name=requested_job_name,
                table_name=requested_job_name,
                written_tables=(requested_job_name,),
                trigger_stock_bi_sync=requested_job_name == "stock_daily",
                params={"trade_date": "20260313"},
                rows_fetched=123,
                rows_written=123,
            )
        ]

    def fake_sync_stock_bi(trade_date: str):
        events.append(f"stock_bi:{trade_date}")
        return {"status": "ok", "trade_date": trade_date}

    def fake_trigger_stock_bi_v1_precompute(trade_date: str):
        events.append(f"stock_bi_v1:{trade_date}")
        return {"status": "accepted", "trade_date": trade_date}

    monkeypatch.setattr(daily_runner, "run_configured_jobs", fake_run_configured_jobs)
    monkeypatch.setattr(daily_runner, "sync_stock_bi", fake_sync_stock_bi)
    monkeypatch.setattr(daily_runner, "trigger_stock_bi_v1_precompute", fake_trigger_stock_bi_v1_precompute)

    exit_code = daily_runner.main(["--jobs", "stock_daily", "--as-of", "2026-03-14"])

    assert exit_code == 0
    assert events == ["run:stock_daily", "stock_bi:20260313"]


def test_run_jobs_rejects_unknown_job_name():
    class FakeFetcher:
        def fetch(self, **kwargs):
            return pd.DataFrame([{"trade_date": "20260313"}])

    class FakeWriter:
        def write(self, job_definition, frame):
            return len(frame.index)

    jobs = [
        runtime.JobDefinition(
            name="stock_daily",
            fetcher_cls=FakeFetcher,
            table_name="stock_daily",
            params={"trade_date": "{{ trade_date_compact }}"},
            scope_columns=("trade_date",),
        )
    ]
    context = runtime.ExecutionContext(as_of_date=date(2026, 3, 14), trade_date=date(2026, 3, 13))

    with pytest.raises(ValueError, match="Unknown job names"):
        runtime.run_jobs(jobs, context=context, writer=FakeWriter(), job_names=["missing_job"])

from __future__ import annotations

import types
from pathlib import Path

import pandas as pd
import pytest

from apps.data_hub.data_pipeline_ts.analysis import run_strategy_suite as module
from apps.data_hub.data_pipeline_ts.analysis.strategy_registry import StrategySpec


def test_main_prints_suite_context_and_result_paths(monkeypatch, tmp_path: Path, capsys):
    captured = {}
    monkeypatch.setattr(module.time, "strftime", lambda fmt, ts=None: "0423_1030")

    def fake_run_suite(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "suite_summary_df": pd.DataFrame([{"strategy_name": "bottom_volume_matrix"}]),
            "output_paths": {
                "suite_summary_csv": kwargs["output_dir"] / "suite_summary.csv",
                "suite_compact_ranking_csv": kwargs["output_dir"] / "suite_compact_ranking.csv",
                "suite_compact_by_strategy_csv": kwargs["output_dir"] / "suite_compact_by_strategy.csv",
            },
        }

    monkeypatch.setattr(module, "run_suite", fake_run_suite)

    exit_code = module.main(
        [
            "--start-date",
            "20240101",
            "--end-date",
            "20240131",
            "--strategies",
            "bottom_volume_matrix,limit_inst_matrix",
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured["kwargs"] == {
        "start_date": "20240101",
        "end_date": "20240131",
        "strategy_names": ["bottom_volume_matrix", "limit_inst_matrix"],
        "min_sample": 30,
        "top_n": 20,
        "output_dir": tmp_path / "0423_1030",
    }
    assert "suite = strategy_suite" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert "strategies = bottom_volume_matrix,limit_inst_matrix" in stdout
    assert f"output_dir = {tmp_path / '0423_1030'}" in stdout
    assert "==> suite_summary_csv = " in stdout
    assert "==> suite_compact_ranking_csv = " in stdout
    assert "==> suite_compact_by_strategy_csv = " in stdout
    assert "==> strategy_count = 1" in stdout


def test_resolve_strategy_specs_defaults_to_all_registered():
    specs = module.resolve_strategy_specs(None)
    assert [item.strategy_name for item in specs] == [
        "bottom_volume_matrix",
        "flow_chip_northbound_matrix",
        "limit_inst_matrix",
        "supply_shock_matrix",
        "top_list_matrix",
    ]


def test_resolve_strategy_specs_rejects_unknown_names():
    with pytest.raises(ValueError, match="Unknown strategies: foo_matrix"):
        module.resolve_strategy_specs(["bottom_volume_matrix", "foo_matrix"])


def test_load_strategy_module_imports_registered_path(monkeypatch):
    fake_module = types.SimpleNamespace(
        STRATEGY_NAME="bottom_volume_matrix",
        STRATEGY_DESCRIPTION="底部放量策略矩阵",
        run_analysis=lambda **_: {},
    )

    captured = {}

    def fake_import(name: str):
        captured["module_path"] = name
        return fake_module

    monkeypatch.setattr(module.importlib, "import_module", fake_import)

    spec = StrategySpec(
        strategy_name="bottom_volume_matrix",
        strategy_description="底部放量策略矩阵",
        module_path="apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix",
    )
    loaded = module.load_strategy_module(spec)
    assert loaded is fake_module
    assert captured["module_path"] == spec.module_path


def test_run_single_strategy_success_builds_summary_row(tmp_path: Path):
    fake_module = types.SimpleNamespace(
        STRATEGY_NAME="bottom_volume_matrix",
        STRATEGY_DESCRIPTION="底部放量策略矩阵",
        run_analysis=lambda **kwargs: {
            "compact_df": pd.DataFrame([{"signal_code": "demo"}]),
            "output_paths": {
                "summary_csv": tmp_path / "bottom_volume_matrix" / "0423_1200.csv",
                "summary_md": tmp_path / "bottom_volume_matrix" / "0423_1200.md",
            },
        },
    )

    spec = StrategySpec(
        strategy_name="bottom_volume_matrix",
        strategy_description="底部放量策略矩阵",
        module_path="demo.path",
    )
    result = module.run_single_strategy(
        spec=spec,
        strategy_module=fake_module,
        start_date="20240101",
        end_date="20240131",
        min_sample=30,
        top_n=20,
        suite_output_dir=tmp_path,
    )

    assert result["strategy_name"] == "bottom_volume_matrix"
    assert result["status"] == "success"
    assert result["rows"] == 1
    assert result["summary_csv"].endswith("bottom_volume_matrix/0423_1200.csv")
    assert result["summary_md"].endswith("bottom_volume_matrix/0423_1200.md")
    assert result["error_message"] == ""


def test_run_single_strategy_failure_keeps_summary_row(tmp_path: Path):
    def boom(**kwargs):
        raise RuntimeError("db offline")

    fake_module = types.SimpleNamespace(
        STRATEGY_NAME="limit_inst_matrix",
        STRATEGY_DESCRIPTION="涨跌停 + 龙虎榜事件矩阵",
        run_analysis=boom,
    )
    spec = StrategySpec(
        strategy_name="limit_inst_matrix",
        strategy_description="涨跌停 + 龙虎榜事件矩阵",
        module_path="demo.path",
    )

    result = module.run_single_strategy(
        spec=spec,
        strategy_module=fake_module,
        start_date="20240101",
        end_date="20240131",
        min_sample=30,
        top_n=20,
        suite_output_dir=tmp_path,
    )

    assert result["strategy_name"] == "limit_inst_matrix"
    assert result["status"] == "failed"
    assert result["rows"] == 0
    assert result["summary_csv"] == ""
    assert result["summary_md"] == ""
    assert result["error_message"] == "RuntimeError: db offline"


def test_build_suite_summary_frame_keeps_success_and_failure_rows():
    frame = module.build_suite_summary_frame(
        [
            {
                "strategy_name": "bottom_volume_matrix",
                "strategy_description": "底部放量策略矩阵",
                "status": "success",
                "rows": 10,
                "summary_csv": "/tmp/a.csv",
                "summary_md": "/tmp/a.md",
                "elapsed_seconds": 1.2,
                "error_message": "",
            },
            {
                "strategy_name": "limit_inst_matrix",
                "strategy_description": "涨跌停 + 龙虎榜事件矩阵",
                "status": "failed",
                "rows": 0,
                "summary_csv": "",
                "summary_md": "",
                "elapsed_seconds": 0.4,
                "error_message": "RuntimeError: db offline",
            },
        ]
    )

    assert list(frame["strategy_name"]) == ["bottom_volume_matrix", "limit_inst_matrix"]
    assert list(frame["status"]) == ["success", "failed"]


def test_build_suite_compact_frames_filters_failed_and_zero_row_results():
    success_with_rows = {
        "strategy_name": "bottom_volume_matrix",
        "strategy_description": "底部放量策略矩阵",
        "status": "success",
        "rows": 2,
        "compact_df": pd.DataFrame(
            [
                {
                    "signal_code": "a",
                    "sample_count": 20,
                    "win_rate_1d": 0.8,
                    "avg_ret_1d": 0.05,
                    "win_rate_3d": 0.7,
                    "avg_ret_3d": 0.06,
                },
                {
                    "signal_code": "b",
                    "sample_count": 10,
                    "win_rate_1d": 0.7,
                    "avg_ret_1d": 0.04,
                    "win_rate_3d": 0.6,
                    "avg_ret_3d": 0.05,
                },
            ]
        ),
    }
    success_empty = {
        "strategy_name": "limit_inst_matrix",
        "strategy_description": "涨跌停 + 龙虎榜事件矩阵",
        "status": "success",
        "rows": 0,
        "compact_df": pd.DataFrame(),
    }
    failed = {
        "strategy_name": "top_list_matrix",
        "strategy_description": "龙虎榜策略矩阵",
        "status": "failed",
        "rows": 0,
        "compact_df": pd.DataFrame(),
    }

    ranking_df, by_strategy_df = module.build_suite_compact_frames(
        [success_with_rows, success_empty, failed]
    )

    assert list(ranking_df["strategy_name"]) == ["bottom_volume_matrix", "bottom_volume_matrix"]
    assert list(ranking_df["signal_code"]) == ["a", "b"]
    assert list(by_strategy_df["strategy_name"]) == ["bottom_volume_matrix", "bottom_volume_matrix"]


def test_build_suite_compact_frames_returns_stable_schema_for_empty_input():
    ranking_df, by_strategy_df = module.build_suite_compact_frames(
        [
            {
                "strategy_name": "bottom_volume_matrix",
                "strategy_description": "底部放量策略矩阵",
                "status": "success",
                "rows": 0,
                "compact_df": pd.DataFrame(),
            },
            {
                "strategy_name": "limit_inst_matrix",
                "strategy_description": "涨跌停 + 龙虎榜事件矩阵",
                "status": "failed",
                "rows": 0,
                "compact_df": pd.DataFrame(),
            },
        ]
    )

    expected_columns = [
        "signal_code",
        "sample_count",
        "win_rate_1d",
        "avg_ret_1d",
        "win_rate_3d",
        "avg_ret_3d",
        "strategy_name",
        "strategy_description",
    ]

    assert list(ranking_df.columns) == expected_columns
    assert list(by_strategy_df.columns) == expected_columns
    assert ranking_df.empty
    assert by_strategy_df.empty


def test_write_suite_compact_outputs_writes_both_csvs(tmp_path: Path):
    ranking_df = pd.DataFrame([{"strategy_name": "bottom_volume_matrix", "signal_code": "a"}])
    by_strategy_df = pd.DataFrame([{"strategy_name": "bottom_volume_matrix", "signal_code": "a"}])

    output_paths = module.write_suite_compact_outputs(
        ranking_df=ranking_df,
        by_strategy_df=by_strategy_df,
        output_dir=tmp_path,
    )

    assert output_paths["suite_compact_ranking_csv"].exists()
    assert output_paths["suite_compact_by_strategy_csv"].exists()


def test_run_suite_executes_multiple_strategies_and_writes_outputs(monkeypatch, tmp_path: Path):
    fake_specs = [
        StrategySpec(
            strategy_name="bottom_volume_matrix",
            strategy_description="底部放量策略矩阵",
            module_path="demo.bottom",
        ),
        StrategySpec(
            strategy_name="limit_inst_matrix",
            strategy_description="涨跌停 + 龙虎榜事件矩阵",
            module_path="demo.limit",
        ),
    ]

    fake_modules = {
        "bottom_volume_matrix": type(
            "BottomModule",
            (),
            {
                "STRATEGY_NAME": "bottom_volume_matrix",
                "STRATEGY_DESCRIPTION": "底部放量策略矩阵",
                "run_analysis": staticmethod(
                    lambda **kwargs: {
                        "compact_df": pd.DataFrame(
                            [
                                {
                                    "signal_code": "alpha",
                                    "sample_count": 12,
                                    "win_rate_1d": 0.75,
                                    "avg_ret_1d": 0.04,
                                    "win_rate_3d": 0.70,
                                    "avg_ret_3d": 0.05,
                                }
                            ]
                        ),
                        "output_paths": {
                            "summary_csv": kwargs["output_dir"] / "0423_1200.csv",
                            "summary_md": kwargs["output_dir"] / "0423_1200.md",
                        },
                    }
                ),
            },
        ),
        "limit_inst_matrix": type(
            "LimitModule",
            (),
            {
                "STRATEGY_NAME": "limit_inst_matrix",
                "STRATEGY_DESCRIPTION": "涨跌停 + 龙虎榜事件矩阵",
                "run_analysis": staticmethod(lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db offline"))),
            },
        ),
    }

    monkeypatch.setattr(module, "resolve_strategy_specs", lambda strategy_names: fake_specs)
    monkeypatch.setattr(module, "load_strategy_module", lambda spec: fake_modules[spec.strategy_name])

    result = module.run_suite(
        start_date="20240101",
        end_date="20240131",
        strategy_names=["bottom_volume_matrix", "limit_inst_matrix"],
        min_sample=30,
        top_n=20,
        output_dir=tmp_path / "0423_1030",
    )

    summary_df = result["suite_summary_df"]
    ranking_df = result["suite_compact_ranking_df"]
    by_strategy_df = result["suite_compact_by_strategy_df"]
    output_paths = result["output_paths"]
    suite_run_dir = tmp_path / "0423_1030"

    assert list(summary_df["strategy_name"]) == ["bottom_volume_matrix", "limit_inst_matrix"]
    assert list(summary_df["status"]) == ["success", "failed"]
    assert list(ranking_df["strategy_name"]) == ["bottom_volume_matrix"]
    assert list(by_strategy_df["strategy_name"]) == ["bottom_volume_matrix"]
    assert output_paths["suite_summary_csv"] == suite_run_dir / "suite_summary.csv"
    assert output_paths["suite_compact_ranking_csv"] == suite_run_dir / "suite_compact_ranking.csv"
    assert output_paths["suite_compact_by_strategy_csv"] == suite_run_dir / "suite_compact_by_strategy.csv"
    assert output_paths["suite_summary_csv"].exists()
    assert output_paths["suite_compact_ranking_csv"].exists()
    assert output_paths["suite_compact_by_strategy_csv"].exists()

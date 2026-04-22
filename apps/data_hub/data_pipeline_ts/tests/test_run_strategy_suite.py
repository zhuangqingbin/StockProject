from __future__ import annotations

import types
from pathlib import Path

import pandas as pd
import pytest

from apps.data_hub.data_pipeline_ts.analysis import run_strategy_suite as module
from apps.data_hub.data_pipeline_ts.analysis.strategy_registry import StrategySpec


def test_main_prints_suite_context_and_result_paths(monkeypatch, tmp_path: Path, capsys):
    captured = {}

    def fake_run_suite(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "suite_summary_df": pd.DataFrame([{"strategy_name": "bottom_volume_matrix"}]),
            "output_paths": {
                "suite_summary_csv": tmp_path / "suite_summary.csv",
                "suite_compact_ranking_csv": tmp_path / "suite_compact_ranking.csv",
                "suite_compact_by_strategy_csv": tmp_path / "suite_compact_by_strategy.csv",
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
        "output_dir": tmp_path,
    }
    assert "suite = strategy_suite" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert "strategies = bottom_volume_matrix,limit_inst_matrix" in stdout
    assert f"output_dir = {tmp_path}" in stdout
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

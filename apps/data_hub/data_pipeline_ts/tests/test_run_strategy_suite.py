from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis import run_strategy_suite as module


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

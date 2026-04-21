from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.top_list_strategies import (
    top_list_matrix as module,
)


def test_main_prints_context_and_result_paths(monkeypatch, tmp_path: Path, capsys):
    captured = {}

    def fake_run_analysis(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "compact_df": pd.DataFrame([{"signal_code": "demo"}]),
            "output_paths": {
                "summary_csv": tmp_path / "0422_1200.csv",
                "summary_md": tmp_path / "0422_1200.md",
            },
        }

    monkeypatch.setattr(module, "run_analysis", fake_run_analysis)

    exit_code = module.main(
        [
            "--start-date",
            "20240101",
            "--end-date",
            "20240131",
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured["kwargs"] == {
        "start_date": "20240101",
        "end_date": "20240131",
        "min_sample": 30,
        "top_n": 20,
        "output_dir": tmp_path,
        "show_progress": True,
    }
    assert "strategy = top_list_matrix" in stdout
    assert "description = 龙虎榜策略矩阵" in stdout
    assert "source_tables = stock_stk_factor_pro, stock_top_inst, stock_top_list" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert f"output_dir = {tmp_path}" in stdout
    assert "==> summary_csv = " in stdout
    assert "==> summary_md = " in stdout
    assert "==> rows = 1" in stdout

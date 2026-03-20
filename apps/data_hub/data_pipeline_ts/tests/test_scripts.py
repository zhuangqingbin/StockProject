from __future__ import annotations

from pathlib import Path


def test_data_pipeline_ts_scripts_are_self_contained():
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"

    run_daily = (scripts_dir / "run_daily.sh").read_text(encoding="utf-8")
    run_backfill = (scripts_dir / "run_backfill.sh").read_text(encoding="utf-8")
    sync_infrastructure = (scripts_dir / "sync_infrastructure.sh").read_text(encoding="utf-8")
    install_launchd = (scripts_dir / "install_launchd.sh").read_text(encoding="utf-8")

    assert "apps.data_hub.data_pipeline_ts.main" in run_daily
    assert "--mode once" not in run_daily
    assert "--mode backfill" in run_backfill
    assert "--mode infrastructure" in sync_infrastructure
    assert "data_pipeline_ts/scripts/run_daily.sh" in install_launchd
    assert "PROFILE_SPECS" in install_launchd
    assert 'install_plan "com.stockproject.stock-data-v1-orchestrator-v2.pre-open"' not in install_launchd
    assert "apps/data_hub/scripts" not in install_launchd
    assert "ORCHESTRATOR_V2_PRECOMPUTE_ENABLED" not in install_launchd
    assert 'REPO_ROOT}/apps/.venv/bin/python' in run_daily
    assert 'REPO_ROOT}/apps/.venv/bin/python' in install_launchd
    assert "apps/data_hub/.venv" not in run_daily
    assert "apps/data_hub/.venv" not in install_launchd

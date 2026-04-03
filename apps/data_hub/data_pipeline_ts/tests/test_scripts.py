from __future__ import annotations

import os
from pathlib import Path
import subprocess


def _run_install_launchd(tmp_path: Path, *args: str) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    script_path = scripts_dir / "install_launchd.sh"
    fake_home = tmp_path / "home"
    fake_bin = tmp_path / "bin"
    fake_home.mkdir()
    fake_bin.mkdir()

    fake_launchctl = fake_bin / "launchctl"
    fake_launchctl.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_launchctl.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    subprocess.run(
        ["bash", str(script_path), *args],
        check=True,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    return fake_home / "Library" / "LaunchAgents"


def test_data_pipeline_ts_scripts_are_self_contained():
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"

    run_daily = (scripts_dir / "run_daily.sh").read_text(encoding="utf-8")
    run_backfill = (scripts_dir / "run_backfill.sh").read_text(encoding="utf-8")
    run_job = (scripts_dir / "run_job.sh").read_text(encoding="utf-8")
    sync_infrastructure = (scripts_dir / "sync_infrastructure.sh").read_text(encoding="utf-8")
    install_launchd = (scripts_dir / "install_launchd.sh").read_text(encoding="utf-8")

    assert "apps.data_hub.data_pipeline_ts.main" in run_daily
    assert "--mode once" not in run_daily
    assert "--mode backfill" in run_backfill
    assert "apps.data_hub.data_pipeline_ts.run_job" in run_job
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


def test_install_launchd_does_not_emit_max_workers_by_default(tmp_path):
    agents_dir = _run_install_launchd(tmp_path)
    plist = (agents_dir / "com.stockproject.stock-data-v1-orchestrator-v2.trade-day-post-close-core.plist").read_text(encoding="utf-8")

    assert "--profiles" in plist
    assert "--max-workers" not in plist


def test_install_launchd_emits_max_workers_when_requested(tmp_path):
    agents_dir = _run_install_launchd(tmp_path, "--max-workers", "1")
    plist = (agents_dir / "com.stockproject.stock-data-v1-orchestrator-v2.trade-day-post-close-core.plist").read_text(encoding="utf-8")

    assert "<string>--max-workers</string>" in plist
    assert "<string>1</string>" in plist

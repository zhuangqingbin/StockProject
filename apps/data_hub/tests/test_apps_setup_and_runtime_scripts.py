from __future__ import annotations

from pathlib import Path


def test_apps_setup_script_bootstraps_shared_apps_venv():
    repo_root = Path(__file__).resolve().parents[3]
    setup_script = repo_root / "apps" / "setup.sh"

    assert setup_script.exists()
    assert (repo_root / "apps" / "requirements.txt").exists()

    content = setup_script.read_text(encoding="utf-8")
    assert "apps/.venv/bin/python" in content
    assert "apps/requirements.txt" in content
    assert "apps/data_hub/requirements.txt" not in content
    assert "apps/data_hub/data_pipeline_ts/requirements.txt" not in content
    assert "apps/data_hub/data_explorer/requirements.txt" not in content


def test_data_hub_setup_script_delegates_to_shared_apps_setup():
    repo_root = Path(__file__).resolve().parents[3]
    setup_script = repo_root / "apps" / "data_hub" / "setup.sh"

    assert setup_script.exists()

    content = setup_script.read_text(encoding="utf-8")
    assert "../setup.sh" in content
    assert "exec" in content


def test_data_explorer_runtime_script_uses_shared_apps_venv():
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "apps" / "data_hub" / "data_explorer" / "scripts" / "run.sh"

    content = script.read_text(encoding="utf-8")
    assert "apps/.venv/bin/python" in content
    assert "apps/data_hub/.venv" not in content


def test_data_hub_readme_documents_all_scheduled_and_manual_commands():
    repo_root = Path(__file__).resolve().parents[3]
    readme = (repo_root / "apps" / "data_hub" / "README.md").read_text(encoding="utf-8")

    scheduled_profiles = (
        "trade_day_pre_open,"
        "trade_day_post_close_core,"
        "trade_day_post_close_extended,"
        "reference_trade_day_post_close,"
        "financial_calendar_nightly,"
        "reference_calendar_nightly"
    )

    assert f"--profiles {scheduled_profiles}" in readme
    assert "run_daily.sh --profiles manual --jobs stock_daily_qfq --as-of 2026-03-16" in readme
    assert "`manual` profile 不支持 backfill" in readme

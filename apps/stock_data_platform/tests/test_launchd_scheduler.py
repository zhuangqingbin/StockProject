from __future__ import annotations

import os
import plistlib
from pathlib import Path

import pytest

from apps.stock_data_platform.jobs import launchd_scheduler


def test_build_launch_agent_plist_contains_expected_schedule_and_paths(tmp_path):
    repo_root = tmp_path / "repo"
    home_dir = tmp_path / "home"

    plist_content = launchd_scheduler.build_launch_agent_plist(
        hour=18,
        minute=30,
        repo_root=repo_root,
        home_dir=home_dir,
    )
    plist_data = plistlib.loads(plist_content.encode("utf-8"))

    assert plist_data["Label"] == launchd_scheduler.DEFAULT_LAUNCHD_LABEL
    assert plist_data["ProgramArguments"] == [
        "/bin/bash",
        str(repo_root / "apps" / "stock_data_platform" / "scripts" / "run_stock_data_daily.sh"),
    ]
    assert plist_data["WorkingDirectory"] == str(repo_root)
    assert plist_data["StartCalendarInterval"] == {"Hour": 18, "Minute": 30}
    assert plist_data["StandardOutPath"] == str(
        repo_root / "apps" / "stock_data_platform" / ".logs" / "stock_data_daily.launchd.out.log"
    )
    assert plist_data["StandardErrorPath"] == str(
        repo_root / "apps" / "stock_data_platform" / ".logs" / "stock_data_daily.launchd.err.log"
    )
    assert plist_data["EnvironmentVariables"]["PATH"].startswith("/usr/bin")


def test_install_launch_agent_writes_plist_and_reloads_launchd(tmp_path):
    repo_root = tmp_path / "repo"
    home_dir = tmp_path / "home"
    calls: list[tuple[list[str], bool]] = []

    def fake_launchctl(args: list[str], check: bool = True) -> None:
        calls.append((args, check))

    agent_path = launchd_scheduler.install_launch_agent(
        hour=7,
        minute=5,
        repo_root=repo_root,
        home_dir=home_dir,
        launchctl_runner=fake_launchctl,
    )

    assert agent_path == (
        home_dir
        / "Library"
        / "LaunchAgents"
        / f"{launchd_scheduler.DEFAULT_LAUNCHD_LABEL}.plist"
    )
    assert agent_path.exists()
    assert (repo_root / "apps" / "stock_data_platform" / ".logs").exists()
    assert calls == [
        (["bootout", f"gui/{os.getuid()}", str(agent_path)], False),
        (["bootstrap", f"gui/{os.getuid()}", str(agent_path)], True),
    ]


def test_build_launch_agent_plist_uses_env_schedule_defaults(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    home_dir = tmp_path / "home"
    monkeypatch.setenv("STOCK_DATA_DAILY_SCHEDULE_HOUR", "21")
    monkeypatch.setenv("STOCK_DATA_DAILY_SCHEDULE_MINUTE", "45")

    plist_content = launchd_scheduler.build_launch_agent_plist(
        repo_root=repo_root,
        home_dir=home_dir,
    )
    plist_data = plistlib.loads(plist_content.encode("utf-8"))

    assert plist_data["StartCalendarInterval"] == {"Hour": 21, "Minute": 45}


@pytest.mark.parametrize(
    ("hour", "minute"),
    [
        (-1, 0),
        (24, 0),
        (0, -1),
        (0, 60),
    ],
)
def test_build_launch_agent_plist_rejects_invalid_schedule_values(hour: int, minute: int):
    with pytest.raises(ValueError):
        launchd_scheduler.build_launch_agent_plist(hour=hour, minute=minute)

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
from pathlib import Path
from typing import Callable

from shared.stock_core.config import get_int


DEFAULT_LAUNCHD_LABEL = "com.stockproject.stock-data-daily"
DEFAULT_SCHEDULE_HOUR = 18
DEFAULT_SCHEDULE_MINUTE = 0
DEFAULT_PATH = "/usr/bin:/bin:/usr/sbin:/sbin:/Library/Developer/CommandLineTools/usr/bin"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_launch_agent_path(home_dir: Path, label: str) -> Path:
    return home_dir / "Library" / "LaunchAgents" / f"{label}.plist"


def _resolve_log_dir(repo_root: Path) -> Path:
    return repo_root / "apps" / "stock_data_platform" / ".logs"


def _resolve_run_script_path(repo_root: Path) -> Path:
    return repo_root / "apps" / "stock_data_platform" / "scripts" / "run_stock_data_daily.sh"


def _validate_schedule(hour: int, minute: int) -> None:
    if not 0 <= hour <= 23:
        raise ValueError(f"hour must be between 0 and 23, got {hour}")
    if not 0 <= minute <= 59:
        raise ValueError(f"minute must be between 0 and 59, got {minute}")


def _resolve_schedule(hour: int | None = None, minute: int | None = None) -> tuple[int, int]:
    resolved_hour = hour
    if resolved_hour is None:
        resolved_hour = get_int("STOCK_DATA_DAILY_SCHEDULE_HOUR", DEFAULT_SCHEDULE_HOUR)

    resolved_minute = minute
    if resolved_minute is None:
        resolved_minute = get_int("STOCK_DATA_DAILY_SCHEDULE_MINUTE", DEFAULT_SCHEDULE_MINUTE)

    _validate_schedule(resolved_hour, resolved_minute)
    return resolved_hour, resolved_minute


def build_launch_agent_plist(
    hour: int | None = None,
    minute: int | None = None,
    repo_root: Path | None = None,
    home_dir: Path | None = None,
    label: str = DEFAULT_LAUNCHD_LABEL,
) -> str:
    resolved_hour, resolved_minute = _resolve_schedule(hour, minute)

    resolved_repo_root = Path(repo_root) if repo_root is not None else _default_repo_root()
    resolved_home_dir = Path(home_dir) if home_dir is not None else Path.home()
    run_script_path = _resolve_run_script_path(resolved_repo_root)
    log_dir = _resolve_log_dir(resolved_repo_root)
    agent_path = _resolve_launch_agent_path(resolved_home_dir, label)

    launch_agent_data = {
        "Label": label,
        "ProgramArguments": ["/bin/bash", str(run_script_path)],
        "WorkingDirectory": str(resolved_repo_root),
        "RunAtLoad": False,
        "StartCalendarInterval": {
            "Hour": resolved_hour,
            "Minute": resolved_minute,
        },
        "StandardOutPath": str(log_dir / "stock_data_daily.launchd.out.log"),
        "StandardErrorPath": str(log_dir / "stock_data_daily.launchd.err.log"),
        "EnvironmentVariables": {
            "HOME": str(resolved_home_dir),
            "PATH": DEFAULT_PATH,
        },
        "ProcessType": "Background",
        "AbandonProcessGroup": True,
        "LaunchOnlyOnce": False,
    }

    plist_bytes = plistlib.dumps(launch_agent_data, sort_keys=False)
    return plist_bytes.decode("utf-8")


def _launchctl_target(uid: int | None = None) -> str:
    return f"gui/{uid if uid is not None else os.getuid()}"


def _run_launchctl(args: list[str], check: bool = True) -> None:
    command = ["launchctl", *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown launchctl error"
        raise RuntimeError(f"launchctl failed: command={' '.join(command)}, reason={stderr}")


def install_launch_agent(
    hour: int | None = None,
    minute: int | None = None,
    repo_root: Path | None = None,
    home_dir: Path | None = None,
    label: str = DEFAULT_LAUNCHD_LABEL,
    launchctl_runner: Callable[[list[str], bool], None] = _run_launchctl,
) -> Path:
    resolved_repo_root = Path(repo_root) if repo_root is not None else _default_repo_root()
    resolved_home_dir = Path(home_dir) if home_dir is not None else Path.home()
    log_dir = _resolve_log_dir(resolved_repo_root)
    agent_path = _resolve_launch_agent_path(resolved_home_dir, label)

    log_dir.mkdir(parents=True, exist_ok=True)
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(
        build_launch_agent_plist(
            hour=hour,
            minute=minute,
            repo_root=resolved_repo_root,
            home_dir=resolved_home_dir,
            label=label,
        ),
        encoding="utf-8",
    )

    target = _launchctl_target()
    launchctl_runner(["bootout", target, str(agent_path)], False)
    launchctl_runner(["bootstrap", target, str(agent_path)], True)
    return agent_path


def uninstall_launch_agent(
    home_dir: Path | None = None,
    label: str = DEFAULT_LAUNCHD_LABEL,
    launchctl_runner: Callable[[list[str], bool], None] = _run_launchctl,
) -> Path:
    resolved_home_dir = Path(home_dir) if home_dir is not None else Path.home()
    agent_path = _resolve_launch_agent_path(resolved_home_dir, label)

    target = _launchctl_target()
    launchctl_runner(["bootout", target, str(agent_path)], False)

    if agent_path.exists():
        agent_path.unlink()

    return agent_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the macOS launchd schedule for stock data daily jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install or update the daily launchd schedule.")
    install_parser.add_argument("--hour", type=int)
    install_parser.add_argument("--minute", type=int)

    uninstall_parser = subparsers.add_parser("uninstall", help="Unload and remove the daily launchd schedule.")
    uninstall_parser.add_argument("--label", default=DEFAULT_LAUNCHD_LABEL)

    print_parser = subparsers.add_parser("print", help="Print the launchd plist without installing it.")
    print_parser.add_argument("--hour", type=int)
    print_parser.add_argument("--minute", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "install":
        agent_path = install_launch_agent(hour=args.hour, minute=args.minute)
        print(f"Installed launchd agent: {agent_path}")
        return 0

    if args.command == "uninstall":
        agent_path = uninstall_launch_agent(label=args.label)
        print(f"Removed launchd agent: {agent_path}")
        return 0

    if args.command == "print":
        print(build_launch_agent_plist(hour=args.hour, minute=args.minute))
        return 0

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

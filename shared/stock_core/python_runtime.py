from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable, Optional, Sequence, Tuple


MINIMUM_PYTHON_VERSION: Tuple[int, int] = (3, 11)
MINIMUM_PYTHON_LABEL = "3.11"
DEFAULT_OVERRIDE_KEYS: Tuple[str, ...] = ("STOCK_PROJECT_PYTHON", "SYSTEM_PYTHON")


def default_python_candidates() -> list[str]:
    return [
        "python3.11",
        "/opt/homebrew/bin/python3.11",
        "/usr/local/bin/python3.11",
        "python3.12",
        "/opt/homebrew/bin/python3.12",
        "/usr/local/bin/python3.12",
        "python3.13",
        "/opt/homebrew/bin/python3.13",
        "/usr/local/bin/python3.13",
        "python3",
    ]


def format_version(version: Sequence[int]) -> str:
    return ".".join(str(part) for part in version)


def is_supported_python(version: Optional[Sequence[int]]) -> bool:
    if version is None or len(version) < 2:
        return False
    return tuple(version[:2]) >= MINIMUM_PYTHON_VERSION


def _resolve_candidate(candidate: str, which: Callable[[str], Optional[str]]) -> Optional[str]:
    if os.path.isabs(candidate):
        return candidate if os.path.exists(candidate) else None
    return which(candidate)


def probe_python_version(python_command: str) -> Optional[Tuple[int, int, int]]:
    result = subprocess.run(
        [
            python_command,
            "-c",
            "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    raw_value = result.stdout.strip()
    parts = raw_value.split(".")
    if len(parts) != 3:
        return None

    try:
        major, minor, micro = (int(part) for part in parts)
    except ValueError:
        return None

    return major, minor, micro


def resolve_python_command(
    explicit: Optional[str] = None,
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
    probe: Callable[[str], Optional[Tuple[int, int, int]]] = probe_python_version,
    candidates: Optional[Sequence[str]] = None,
) -> str:
    ordered_candidates: list[str] = []
    if explicit:
        ordered_candidates.append(explicit)

    for candidate in candidates or default_python_candidates():
        if candidate not in ordered_candidates:
            ordered_candidates.append(candidate)

    for index, candidate in enumerate(ordered_candidates):
        resolved = _resolve_candidate(candidate, which)
        if not resolved:
            continue

        version = probe(resolved)
        if is_supported_python(version):
            return resolved

        if explicit and index == 0:
            version_label = format_version(version) if version else "unknown"
            raise RuntimeError(
                f"Python {MINIMUM_PYTHON_LABEL} or newer is required, but {resolved} reports {version_label}."
            )

    if explicit:
        raise RuntimeError(f"Explicit Python override {explicit!r} was not found or is not executable.")

    raise RuntimeError(
        "Could not find a Python 3.11+ interpreter. "
        "Install python3.11 or set STOCK_PROJECT_PYTHON to an explicit 3.11+ path."
    )


def resolve_python_from_env(
    environ: Optional[dict[str, str]] = None,
    *,
    override_keys: Sequence[str] = DEFAULT_OVERRIDE_KEYS,
    which: Callable[[str], Optional[str]] = shutil.which,
    probe: Callable[[str], Optional[Tuple[int, int, int]]] = probe_python_version,
    candidates: Optional[Sequence[str]] = None,
) -> str:
    environ = environ if environ is not None else os.environ

    explicit = None
    for key in override_keys:
        value = environ.get(key)
        if value:
            explicit = value
            break

    return resolve_python_command(
        explicit=explicit,
        which=which,
        probe=probe,
        candidates=candidates,
    )


__all__ = [
    "DEFAULT_OVERRIDE_KEYS",
    "MINIMUM_PYTHON_LABEL",
    "MINIMUM_PYTHON_VERSION",
    "default_python_candidates",
    "format_version",
    "is_supported_python",
    "probe_python_version",
    "resolve_python_command",
    "resolve_python_from_env",
]

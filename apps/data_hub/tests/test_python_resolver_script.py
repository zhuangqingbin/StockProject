from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_resolve_project_python_script_returns_executable_path():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "shared" / "scripts" / "resolve_project_python.sh"

    result = subprocess.run(
        [str(script_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
    )

    assert result.returncode == 0, result.stderr

    resolved_python = result.stdout.strip()
    assert resolved_python
    assert Path(resolved_python).exists()

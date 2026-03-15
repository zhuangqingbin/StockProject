from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

from apps.stock_backtest.backend.infrastructure.settings import get_settings


@dataclass
class NotebookRuntimeState:
    process: Optional[subprocess.Popen] = None
    url: Optional[str] = None


runtime_state = NotebookRuntimeState()


def list_notebook_templates() -> list[dict]:
    templates_dir = get_settings().notebooks_dir
    if not templates_dir.exists():
        return [
            {"name": "strategy_dev_template.ipynb", "label": "策略开发模板"},
            {"name": "data_explore_template.ipynb", "label": "数据探索模板"},
            {"name": "result_analysis_template.ipynb", "label": "结果分析模板"},
        ]
    return [{"name": path.name, "label": path.stem.replace("_", " ")} for path in sorted(templates_dir.glob("*.ipynb"))]


def get_notebook_status() -> dict:
    process = runtime_state.process
    if process is not None and process.poll() is None:
        return {"status": "running", "url": runtime_state.url}
    return {"status": "stopped", "url": None}


def start_notebook() -> dict:
    if runtime_state.process is not None and runtime_state.process.poll() is None:
        return {"status": "running", "url": runtime_state.url}

    executable = shutil.which("jupyter-lab")
    if executable is None:
        return {"status": "unavailable", "url": None}

    settings = get_settings()
    process = subprocess.Popen(
        [
            executable,
            "--no-browser",
            "--ServerApp.token=",
            f"--port={settings.notebook_port}",
            str(settings.notebooks_dir),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    runtime_state.process = process
    runtime_state.url = f"http://127.0.0.1:{settings.notebook_port}/lab"
    return {"status": "running", "url": runtime_state.url}


def stop_notebook() -> dict:
    process = runtime_state.process
    if process is not None and process.poll() is None:
        process.terminate()
    runtime_state.process = None
    runtime_state.url = None
    return {"status": "stopped", "url": None}

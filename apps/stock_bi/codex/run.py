#!/usr/bin/env python3
"""
Stock BI 启动脚本
"""
import os
import sys
from pathlib import Path

from launch_env import build_runtime_env, ensure_local_runtime, should_reexec

APP_DIR = Path(__file__).resolve().parent
PATHS = ensure_local_runtime(APP_DIR)

if should_reexec(sys.executable, str(PATHS["venv_python"])):
    os.execve(
        str(PATHS["venv_python"]),
        [str(PATHS["venv_python"]), __file__, *sys.argv[1:]],
        build_runtime_env(os.environ, str(PATHS["repo_root"])),
    )

sys.path.insert(0, str(PATHS["repo_root"]))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Stock BI - A股数据可视化平台")
    print("=" * 60)
    print()
    print("  Frontend: http://localhost:8000/")
    print("  API Docs: http://localhost:8000/api/docs")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(APP_DIR)],
    )

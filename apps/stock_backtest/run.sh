#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${ROOT_DIR}/../.." && pwd)"
MODE="${1:-backend}"
SYSTEM_PYTHON="${SYSTEM_PYTHON:-python3}"
FRONTEND_DIR="${ROOT_DIR}/frontend"
FRONTEND_DIST_INDEX="${FRONTEND_DIR}/dist/index.html"
BACKEND_PROCESS_PATTERN="$(
  PROJECT_ROOT="${PROJECT_ROOT}" "${SYSTEM_PYTHON}" - <<'PY'
from apps.stock_backtest.common.launcher_runtime import backend_process_pattern

print(backend_process_pattern())
PY
)"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

VENV_ARCH="$(
  PROJECT_ROOT="${PROJECT_ROOT}" "${SYSTEM_PYTHON}" - <<'PY'
import os
from pathlib import Path

from apps.stock_backtest.common.venv_runtime import current_arch, default_venv_link, venv_dir

repo_root = Path(os.environ["PROJECT_ROOT"])
arch = current_arch()
print(arch)
PY
)"
VENV_PATH="$(
  PROJECT_ROOT="${PROJECT_ROOT}" VENV_ARCH="${VENV_ARCH}" "${SYSTEM_PYTHON}" - <<'PY'
import os
from pathlib import Path

from apps.stock_backtest.common.venv_runtime import venv_dir

repo_root = Path(os.environ["PROJECT_ROOT"])
print(venv_dir(repo_root, os.environ["VENV_ARCH"]))
PY
)"
DEFAULT_VENV_LINK="$(
  PROJECT_ROOT="${PROJECT_ROOT}" "${SYSTEM_PYTHON}" - <<'PY'
import os
from pathlib import Path

from apps.stock_backtest.common.venv_runtime import default_venv_link

repo_root = Path(os.environ["PROJECT_ROOT"])
print(default_venv_link(repo_root))
PY
)"

if [[ ! -d "${VENV_PATH}" ]]; then
  "${SYSTEM_PYTHON}" -m venv "${VENV_PATH}"
  "${VENV_PATH}/bin/pip" install --upgrade pip setuptools wheel
  "${VENV_PATH}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"
fi

ln -sfn "${VENV_PATH}" "${DEFAULT_VENV_LINK}"

if [[ "${MODE}" == "frontend" ]]; then
  cd "${FRONTEND_DIR}"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run dev
  exit 0
fi

if [[ ! -f "${FRONTEND_DIST_INDEX}" ]]; then
  cd "${FRONTEND_DIR}"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run build
fi

pkill -f "${BACKEND_PROCESS_PATTERN}" >/dev/null 2>&1 || true

echo "Using stock_backtest venv (${VENV_ARCH}): ${VENV_PATH}"
"${VENV_PATH}/bin/uvicorn" apps.stock_backtest.backend.main:app --reload --host 0.0.0.0 --port "${PORT:-8100}"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SYSTEM_PYTHON="/Library/Developer/CommandLineTools/usr/bin/python3"

cd "${REPO_ROOT}"

RUNTIME_INFO="$("${SYSTEM_PYTHON}" - <<'PY'
from pathlib import Path

from apps.stock_data_platform.common.venv_runtime import current_arch, python_bin

arch = current_arch()
print(f"{arch}|{python_bin(Path.cwd(), arch)}")
PY
)"

IFS='|' read -r TARGET_ARCH TARGET_PYTHON <<< "${RUNTIME_INFO}"
TARGET_VENV="$(cd "$(dirname "${TARGET_PYTHON}")/.." && pwd)"

if [[ ! -x "${TARGET_PYTHON}" ]]; then
  echo "Missing stock_data_platform venv for ${TARGET_ARCH}: ${TARGET_VENV}" >&2
  echo "Run: bash apps/stock_data_platform/scripts/setup_stock_data_daily_env.sh" >&2
  exit 1
fi

if [[ "${1-}" == "--print-python" ]]; then
  echo "${TARGET_PYTHON}"
  exit 0
fi

if [[ "${1-}" == "--print-arch" ]]; then
  echo "${TARGET_ARCH}"
  exit 0
fi

export PYTHONNOUSERSITE=1
exec "${TARGET_PYTHON}" "$@"

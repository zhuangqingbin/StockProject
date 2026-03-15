#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SYSTEM_PYTHON="/Library/Developer/CommandLineTools/usr/bin/python3"

cd "${REPO_ROOT}"

if [[ ! -x "${SYSTEM_PYTHON}" ]]; then
  echo "Missing system python: ${SYSTEM_PYTHON}" >&2
  echo "Run: bash apps/stock_data_platform/scripts/setup_stock_data_daily_env.sh" >&2
  exit 1
fi

export PYTHONNOUSERSITE=1
"${SYSTEM_PYTHON}" -m apps.stock_data_platform.notebooks.jupyter_runtime "$@"

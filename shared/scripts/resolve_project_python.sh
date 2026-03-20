#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP_PYTHON="${BOOTSTRAP_PYTHON:-python3}"

if ! command -v "${BOOTSTRAP_PYTHON}" >/dev/null 2>&1 && [[ ! -x "${BOOTSTRAP_PYTHON}" ]]; then
  echo "Missing bootstrap Python: ${BOOTSTRAP_PYTHON}" >&2
  echo "Install Python 3.11+ and make a bootstrap python3 available." >&2
  exit 1
fi

cd "${REPO_ROOT}"

PYTHONNOUSERSITE=1 \
  STOCK_PROJECT_PYTHON="${STOCK_PROJECT_PYTHON:-${SYSTEM_PYTHON:-}}" \
  "${BOOTSTRAP_PYTHON}" - <<'PY'
from shared.stock_core.python_runtime import resolve_python_from_env

print(resolve_python_from_env())
PY

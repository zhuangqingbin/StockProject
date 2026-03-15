#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
PYTHON_LAUNCHER="${REPO_ROOT}/apps/stock_data_platform/scripts/dispatch_stock_data_python.sh"
PATH_VALUE="/usr/bin:/bin:/usr/sbin:/sbin:/Library/Developer/CommandLineTools/usr/bin"

cd "${REPO_ROOT}"

if [[ ! -x "${PYTHON_LAUNCHER}" ]]; then
  echo "Missing Python launcher: ${PYTHON_LAUNCHER}" >&2
  echo "Run: bash apps/stock_data_platform/scripts/setup_stock_data_daily_env.sh" >&2
  exit 1
fi

ENV_ARGS=(
  "HOME=${HOME}"
  "PATH=${PATH_VALUE}"
  "PYTHONNOUSERSITE=1"
  "STOCK_BI_SYNC_PORT_SCAN_COUNT=${STOCK_BI_SYNC_PORT_SCAN_COUNT:-20}"
  "STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT=${STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT:-20}"
)

for passthrough_var in \
  STOCK_BI_SYNC_ENABLED \
  STOCK_BI_SYNC_URL \
  STOCK_BI_SYNC_TIMEOUT_SEC \
  STOCK_BI_SYNC_PORT_SCAN_COUNT \
  STOCK_BI_V1_PRECOMPUTE_ENABLED \
  STOCK_BI_V1_PRECOMPUTE_URL \
  STOCK_BI_V1_PRECOMPUTE_TIMEOUT_SEC \
  STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT; do
  if [[ -n "${!passthrough_var-}" ]]; then
    ENV_ARGS+=("${passthrough_var}=${!passthrough_var}")
  fi
done

env -i \
  "${ENV_ARGS[@]}" \
  "${PYTHON_LAUNCHER}" \
  -m apps.stock_data_platform.jobs.daily_runner \
  "$@"

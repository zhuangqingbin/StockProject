#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
PYTHON_RESOLVER="${REPO_ROOT}/shared/scripts/resolve_project_python.sh"
if [[ ! -x "${PYTHON_RESOLVER}" ]]; then
  echo "Missing Python resolver: ${PYTHON_RESOLVER}" >&2
  exit 1
fi

PROJECT_PYTHON=""
for candidate in \
  "${REPO_ROOT}/apps/.venv/bin/python"; do
  if [[ -x "${candidate}" ]]; then
    PROJECT_PYTHON="${candidate}"
    break
  fi
done

if [[ -z "${PROJECT_PYTHON}" ]]; then
  PROJECT_PYTHON="$("${PYTHON_RESOLVER}")"
fi

cd "${REPO_ROOT}"

export QV_RESEARCH_AUTO_PUBLISH_ENABLED="${QV_RESEARCH_AUTO_PUBLISH_ENABLED:-1}"
export QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION="${QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION:-1}"

PYTHONNOUSERSITE=1 "${PROJECT_PYTHON}" -m apps.data_hub.data_pipeline_ts.main \
  "$@"

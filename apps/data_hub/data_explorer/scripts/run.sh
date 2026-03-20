#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
APP_MODULE="apps.data_hub.data_explorer.backend.main:app"
FRONTEND_DIR="${REPO_ROOT}/apps/data_hub/data_explorer/frontend"
MODE="${1:-backend}"

if [[ -x "${REPO_ROOT}/apps/.venv/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/apps/.venv/bin/python"
elif [[ -x "${REPO_ROOT}/shared/scripts/resolve_project_python.sh" ]]; then
  PYTHON_BIN="$("${REPO_ROOT}/shared/scripts/resolve_project_python.sh")"
else
  PYTHON_BIN="${REPO_ROOT}/apps/.venv/bin/python"
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3 || command -v python)"
fi

run_backend() {
  PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_BIN}" -m uvicorn "${APP_MODULE}" --host 127.0.0.1 --port 8201 --reload
}

run_frontend() {
  npm --prefix "${FRONTEND_DIR}" run dev -- --host 127.0.0.1 --port 5178
}

case "${MODE}" in
  backend)
    run_backend
    ;;
  frontend)
    run_frontend
    ;;
  dev|all)
    run_backend &
    BACKEND_PID=$!
    cleanup() {
      kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    }
    trap cleanup EXIT INT TERM
    run_frontend
    ;;
  *)
    echo "Usage: $0 [backend|frontend|dev]" >&2
    exit 1
    ;;
esac

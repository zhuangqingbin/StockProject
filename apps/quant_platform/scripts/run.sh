#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$APP_DIR/../.." && pwd)"

cd "$APP_DIR"

# Activate shared venv if available
if [ -f "$PROJECT_ROOT/apps/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/apps/.venv/bin/activate"
fi

MODE="${1:-backend}"

case "$MODE" in
    backend)
        echo "Starting QuantViz backend on port ${QV_API_PORT:-8202}..."
        uvicorn app.main:app \
            --host "${QV_API_HOST:-0.0.0.0}" \
            --port "${QV_API_PORT:-8202}" \
            --reload
        ;;
    frontend)
        echo "Starting QuantViz frontend dev server..."
        cd "$APP_DIR/frontend"
        npm run dev
        ;;
    init)
        echo "Initializing database and downloading stock list..."
        python scripts/init_db.py
        ;;
    download)
        shift
        echo "Batch downloading historical data..."
        python scripts/batch_download.py "$@"
        ;;
    update)
        echo "Running daily update..."
        python scripts/daily_update.py
        ;;
    *)
        echo "Usage: $0 {backend|frontend|init|download|update}"
        echo ""
        echo "  backend   - Start FastAPI backend (default)"
        echo "  frontend  - Start Vite dev server"
        echo "  init      - Initialize DB + download stock list"
        echo "  download  - Batch download historical data"
        echo "  update    - Run daily data update"
        exit 1
        ;;
esac

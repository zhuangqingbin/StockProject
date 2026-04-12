#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$APP_DIR/../.." && pwd)"

cd "$APP_DIR"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

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
    research-single)
        shift
        echo "Running single-factor research..."
        cd "$PROJECT_ROOT"
        python -m apps.quant_platform.research.scripts.run_single_factor "$@"
        ;;
    research-factor)
        shift
        echo "Running multi-factor research..."
        cd "$PROJECT_ROOT"
        python -m apps.quant_platform.research.scripts.run_factor_research "$@"
        ;;
    research-publish)
        shift
        echo "Publishing research serving snapshot..."
        cd "$PROJECT_ROOT"
        python -m apps.quant_platform.research.scripts.run_research_publish "$@"
        ;;
    research-backtest)
        shift
        echo "Running factor strategy backtest..."
        cd "$PROJECT_ROOT"
        python -m apps.quant_platform.research.scripts.run_strategy_backtest "$@"
        ;;
    research-notebook)
        echo "Starting JupyterLab for research notebooks..."
        cd "$APP_DIR/research"
        jupyter lab
        ;;
    *)
        echo "Usage: $0 {backend|frontend|init|download|update|research-single|research-factor|research-publish|research-backtest|research-notebook}"
        echo ""
        echo "  backend   - Start FastAPI backend (default)"
        echo "  frontend  - Start Vite dev server"
        echo "  init      - Initialize DB + download stock list"
        echo "  download  - Batch download historical data"
        echo "  update    - Run daily data update"
        echo "  research-single   - Run a single-factor analysis"
        echo "  research-factor   - Run multi-factor ranking research"
        echo "  research-publish  - Publish research serving snapshot for the frontend"
        echo "  research-backtest - Run composite factor backtest"
        echo "  research-notebook - Start JupyterLab in research/"
        exit 1
        ;;
esac

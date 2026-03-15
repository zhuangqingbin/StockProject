from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.infrastructure.database import get_db_session
from apps.stock_backtest.backend.models.api_models import BacktestDailyResponse, BacktestTradeResponse

from .repository import AnalysisRepository
from .service import build_compare_payload, build_industry_exposure, build_rolling_metric, get_run_or_404


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{run_id}/daily", response_model=list[BacktestDailyResponse])
def get_daily_series(
    run_id: int,
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    session: Session = Depends(get_db_session),
):
    get_run_or_404(session, run_id)
    repository = AnalysisRepository(session)
    return repository.list_daily(run_id, start=start, end=end)


@router.get("/{run_id}/trades", response_model=list[BacktestTradeResponse])
def get_trade_series(run_id: int, session: Session = Depends(get_db_session)):
    get_run_or_404(session, run_id)
    repository = AnalysisRepository(session)
    return repository.list_trades(run_id)


@router.get("/{run_id}/positions")
def get_positions(run_id: int, session: Session = Depends(get_db_session)):
    get_run_or_404(session, run_id)
    repository = AnalysisRepository(session)
    return repository.build_positions(run_id)


@router.get("/{run_id}/industry-exposure")
def get_industry_exposure(run_id: int, session: Session = Depends(get_db_session)):
    return build_industry_exposure(session, run_id)


@router.get("/{run_id}/rolling")
def get_rolling_metric(
    run_id: int,
    metric: str = Query(default="sharpe"),
    window: int = Query(default=20, ge=2, le=252),
    session: Session = Depends(get_db_session),
):
    return build_rolling_metric(session, run_id, metric, window)


@router.get("/{run_id}/monthly-returns")
def get_monthly_returns(run_id: int, session: Session = Depends(get_db_session)):
    get_run_or_404(session, run_id)
    repository = AnalysisRepository(session)
    return repository.build_monthly_returns(run_id)


@router.get("/compare")
def compare_runs(run_ids: str = Query(...), session: Session = Depends(get_db_session)):
    parsed_run_ids = [int(item) for item in run_ids.split(",") if item.strip()]
    return build_compare_payload(session, parsed_run_ids)


@router.get("/grid-search/{group_id}")
def get_grid_search(group_id: str, session: Session = Depends(get_db_session)):
    repository = AnalysisRepository(session)
    runs = repository.list_runs_by_group(group_id)
    return [
        {
            "run_id": run.id,
            "annual_return": float(run.annual_return or 0),
            "max_drawdown": float(run.max_drawdown or 0),
            "params": run.params,
        }
        for run in runs
    ]

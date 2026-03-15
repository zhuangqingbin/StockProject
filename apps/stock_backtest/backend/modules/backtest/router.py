from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.infrastructure.database import get_db_session
from apps.stock_backtest.backend.models.api_models import (
    BacktestRunCreateRequest,
    BacktestRunDiagnosticsResponse,
    BacktestRunResponse,
    BacktestRuntimeSummaryResponse,
    BacktestSubmissionResponse,
)
from apps.stock_backtest.backend.models.db_models import RunStatus

from .repository import BacktestRunRepository
from .service import build_run_diagnostics_payload, build_runtime_summary, get_run_or_404, submit_backtest, task_runtime


router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_backtest_route(payload: BacktestRunCreateRequest, session: Session = Depends(get_db_session)):
    run = submit_backtest(session, payload)
    return {"run_id": run.id, "status": run.status, "cache_hit": run.cache_hit, "reused_from_run_id": run.reused_from_run_id}


@router.get("/runtime", response_model=BacktestRuntimeSummaryResponse)
def get_backtest_runtime(session: Session = Depends(get_db_session)):
    return build_runtime_summary(session)


@router.get("/runs", response_model=list[BacktestRunResponse])
def list_backtest_runs(
    strategy_id: Optional[int] = Query(default=None),
    status: Optional[RunStatus] = Query(default=None),
    session: Session = Depends(get_db_session),
):
    repository = BacktestRunRepository(session)
    return repository.list(strategy_id=strategy_id, status=status)


@router.get("/runs/{run_id}", response_model=BacktestRunResponse)
def get_backtest_run(run_id: int, session: Session = Depends(get_db_session)):
    return get_run_or_404(session, run_id)


@router.get("/runs/{run_id}/diagnostics", response_model=BacktestRunDiagnosticsResponse)
def get_backtest_run_diagnostics(run_id: int, session: Session = Depends(get_db_session)):
    return build_run_diagnostics_payload(session, run_id)


@router.post("/runs/{run_id}/cancel")
def cancel_backtest_run(run_id: int, session: Session = Depends(get_db_session)):
    run = get_run_or_404(session, run_id)
    cancelled = task_runtime.cancel(run_id)
    if cancelled:
        run.status = RunStatus.CANCELLED
        run.progress = 100
        session.add(run)
        session.commit()
        session.refresh(run)
    return {"run_id": run_id, "cancelled": cancelled, "status": run.status.value}


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest_run(run_id: int, session: Session = Depends(get_db_session)):
    repository = BacktestRunRepository(session)
    run = get_run_or_404(session, run_id)
    repository.delete(run)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

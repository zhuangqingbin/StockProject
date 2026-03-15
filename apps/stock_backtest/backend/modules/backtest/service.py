from __future__ import annotations

import asyncio
import hashlib
import json
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import date, datetime
from threading import Lock
from typing import Any
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.stock_backtest.backend.engine.runner import run_backtest
from apps.stock_backtest.backend.infrastructure.settings import get_settings
from apps.stock_backtest.backend.models.api_models import BacktestRunCreateRequest
from apps.stock_backtest.backend.models.db_models import RunStatus
from apps.stock_backtest.backend.modules.strategy.service import get_strategy_or_404

from .diagnostics import build_run_event
from .repository import BacktestRunRepository
from .websocket import socket_manager


class BacktestTaskRuntime:
    def __init__(self):
        self._executor: Optional[ProcessPoolExecutor] = None
        self._futures: dict[int, Future] = {}
        self._lock = Lock()

    def start(self) -> None:
        settings = get_settings()
        if settings.execution_mode == "process" and self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=settings.max_workers)

    def shutdown(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
        self._executor = None
        self._futures = {}

    def submit(self, run_id: int) -> None:
        settings = get_settings()
        if settings.execution_mode == "inline":
            result = run_backtest(settings.database_url, run_id)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
            loop.create_task(socket_manager.broadcast({"type": "run_update", **result}))
            return

        self.start()
        if self._executor is None:
            raise RuntimeError("Process pool is not available")
        future = self._executor.submit(run_backtest, settings.database_url, run_id)
        with self._lock:
            self._futures[run_id] = future
        future.add_done_callback(lambda completed: self._cleanup(run_id, completed))

    def cancel(self, run_id: int) -> bool:
        with self._lock:
            future = self._futures.get(run_id)
        if future is None:
            return False
        cancelled = future.cancel()
        if cancelled:
            with self._lock:
                self._futures.pop(run_id, None)
        return cancelled

    def snapshot(self) -> dict[str, list[int]]:
        with self._lock:
            return {"active_run_ids": sorted(self._futures.keys())}

    def _cleanup(self, run_id: int, future: Future) -> None:
        with self._lock:
            self._futures.pop(run_id, None)


task_runtime = BacktestTaskRuntime()


def _normalize_signature_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_signature_value(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [_normalize_signature_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _build_run_signature(strategy, payload: BacktestRunCreateRequest) -> str:
    strategy_signature = {
        "source_type": strategy.source_type.value,
        "template_id": strategy.template_id,
        "code": strategy.code,
        "default_params": strategy.default_params,
        "required_feeds": strategy.required_feeds,
    }
    request_signature = payload.model_dump(exclude={"submitted_by", "grid_search_group_id"})
    signature_payload = {
        "strategy": _normalize_signature_value(strategy_signature),
        "request": _normalize_signature_value(request_signature),
    }
    encoded = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _build_run_payload(payload: BacktestRunCreateRequest, strategy, request_signature: str) -> dict[str, Any]:
    return {
        "strategy_id": payload.strategy_id,
        "params": payload.params,
        "symbols": payload.symbols,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "initial_cash": payload.initial_cash,
        "commission_rate": payload.commission_rate,
        "benchmark": payload.benchmark,
        "data_feeds": payload.data_feeds or strategy.required_feeds,
        "request_signature": request_signature,
        "status": RunStatus.PENDING,
        "progress": 0,
        "cache_hit": False,
        "reused_from_run_id": None,
        "metrics": {},
        "diagnostics": [build_run_event("submitted", "Backtest request accepted", progress=0)],
        "grid_search_group_id": payload.grid_search_group_id,
        "submitted_by": payload.submitted_by,
    }


def _broadcast_update(message: dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(socket_manager.broadcast(message))


def _build_cache_hit_run_payload(base_payload: dict[str, Any], cached_run) -> dict[str, Any]:
    payload = dict(base_payload)
    reused_from_run_id = cached_run.reused_from_run_id or cached_run.id
    payload.update(
        {
            "status": RunStatus.COMPLETED,
            "progress": 100,
            "cache_hit": True,
            "reused_from_run_id": reused_from_run_id,
            "error_message": None,
            "total_return": cached_run.total_return,
            "annual_return": cached_run.annual_return,
            "max_drawdown": cached_run.max_drawdown,
            "sharpe_ratio": cached_run.sharpe_ratio,
            "win_rate": cached_run.win_rate,
            "profit_loss_ratio": cached_run.profit_loss_ratio,
            "metrics": dict(cached_run.metrics or {}),
            "finished_at": datetime.utcnow(),
            "diagnostics": [
                build_run_event("submitted", "Backtest request accepted", progress=0),
                build_run_event(
                    "cache_hit",
                    "Completed run reused from cache",
                    progress=100,
                    metadata={"source_run_id": reused_from_run_id},
                ),
            ],
        }
    )
    return payload


def submit_backtest(session: Session, payload: BacktestRunCreateRequest):
    strategy = get_strategy_or_404(session, payload.strategy_id)
    repository = BacktestRunRepository(session)
    request_signature = _build_run_signature(strategy, payload)
    base_payload = _build_run_payload(payload, strategy, request_signature)
    cached_run = repository.find_completed_by_signature(request_signature)
    if cached_run is not None:
        run = repository.create(_build_cache_hit_run_payload(base_payload, cached_run))
        _broadcast_update(
            {
                "type": "run_update",
                "run_id": run.id,
                "status": run.status.value,
                "metrics": run.metrics,
                "cache_hit": True,
                "reused_from_run_id": run.reused_from_run_id,
            }
        )
        return run

    run = repository.create(base_payload)
    task_runtime.submit(run.id)
    session.refresh(run)
    return run


def build_run_diagnostics_payload(session: Session, run_id: int) -> dict[str, Any]:
    run = get_run_or_404(session, run_id)
    return {
        "run_id": run.id,
        "status": run.status,
        "request_signature": run.request_signature,
        "cache_hit": run.cache_hit,
        "reused_from_run_id": run.reused_from_run_id,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "events": run.diagnostics or [],
    }


def build_runtime_summary(session: Session) -> dict[str, Any]:
    repository = BacktestRunRepository(session)
    runtime_snapshot = task_runtime.snapshot()
    settings = get_settings()
    return {
        "execution_mode": settings.execution_mode,
        "max_workers": settings.max_workers,
        "active_run_ids": runtime_snapshot["active_run_ids"],
        "status_counts": repository.build_status_counts(),
        "cache_hits": repository.count_cache_hits(),
    }


def get_run_or_404(session: Session, run_id: int):
    repository = BacktestRunRepository(session)
    run = repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run

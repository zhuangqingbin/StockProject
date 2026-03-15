from __future__ import annotations

from collections import defaultdict
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.models.db_models import BacktestDailyModel, BacktestRunModel, BacktestTradeModel, MarketStockBasicModel


class AnalysisRepository:
    def __init__(self, session: Session):
        self.session = session

    def _resolve_result_run_id(self, run_id: int) -> int:
        resolved_run_id = run_id
        visited: set[int] = set()

        while resolved_run_id not in visited:
            visited.add(resolved_run_id)
            run = self.get_run(resolved_run_id)
            if run is None or run.reused_from_run_id is None:
                return resolved_run_id
            resolved_run_id = run.reused_from_run_id

        return run_id

    def list_daily(self, run_id: int, start: Optional[date] = None, end: Optional[date] = None) -> list[BacktestDailyModel]:
        effective_run_id = self._resolve_result_run_id(run_id)
        statement = (
            select(BacktestDailyModel)
            .where(BacktestDailyModel.run_id == effective_run_id)
            .order_by(BacktestDailyModel.trade_date.asc())
        )
        if start:
            statement = statement.where(BacktestDailyModel.trade_date >= start)
        if end:
            statement = statement.where(BacktestDailyModel.trade_date <= end)
        return list(self.session.execute(statement).scalars().all())

    def list_trades(self, run_id: int) -> list[BacktestTradeModel]:
        effective_run_id = self._resolve_result_run_id(run_id)
        statement = (
            select(BacktestTradeModel)
            .where(BacktestTradeModel.run_id == effective_run_id)
            .order_by(BacktestTradeModel.trade_date.asc(), BacktestTradeModel.id.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    def list_runs(self, run_ids: list[int]) -> list[BacktestRunModel]:
        statement = select(BacktestRunModel).where(BacktestRunModel.id.in_(run_ids)).order_by(BacktestRunModel.id.asc())
        return list(self.session.execute(statement).scalars().all())

    def get_run(self, run_id: int) -> Optional[BacktestRunModel]:
        return self.session.get(BacktestRunModel, run_id)

    def list_symbols(self, symbols: list[str]) -> dict[str, MarketStockBasicModel]:
        if not symbols:
            return {}
        statement = select(MarketStockBasicModel).where(MarketStockBasicModel.ts_code.in_(symbols))
        rows = self.session.execute(statement).scalars().all()
        return {row.ts_code: row for row in rows}

    def list_runs_by_group(self, group_id: str) -> list[BacktestRunModel]:
        statement = (
            select(BacktestRunModel)
            .where(BacktestRunModel.grid_search_group_id == group_id)
            .order_by(BacktestRunModel.annual_return.desc(), BacktestRunModel.id.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    def build_monthly_returns(self, run_id: int) -> list[dict]:
        daily_rows = self.list_daily(run_id)
        if not daily_rows:
            return []
        frame = pd.DataFrame(
            [{"trade_date": row.trade_date, "daily_return": float(row.daily_return)} for row in daily_rows]
        )
        frame["trade_date"] = pd.to_datetime(frame["trade_date"])
        frame["month"] = frame["trade_date"].dt.strftime("%Y-%m")
        grouped = frame.groupby("month")["daily_return"].apply(lambda values: (values + 1).prod() - 1)
        return [{"month": month, "return": float(value)} for month, value in grouped.items()]

    def build_positions(self, run_id: int) -> list[dict]:
        positions = defaultdict(int)
        for trade in self.list_trades(run_id):
            delta = trade.size if trade.direction.value == "buy" else -trade.size
            positions[trade.symbol] += delta
        return [{"symbol": symbol, "size": size} for symbol, size in positions.items() if size > 0]

from __future__ import annotations

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .repository import AnalysisRepository


def get_run_or_404(session: Session, run_id: int):
    repository = AnalysisRepository(session)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run


def build_compare_payload(session: Session, run_ids: list[int]) -> dict:
    repository = AnalysisRepository(session)
    runs = repository.list_runs(run_ids)
    daily_curves = {}
    for run in runs:
        daily_rows = repository.list_daily(run.id)
        daily_curves[str(run.id)] = [
            {"trade_date": row.trade_date.isoformat(), "cumulative_return": float(row.cumulative_return)}
            for row in daily_rows
        ]
    return {
        "runs": [
            {
                "run_id": run.id,
                "strategy_id": run.strategy_id,
                "annual_return": float(run.annual_return or 0),
                "max_drawdown": float(run.max_drawdown or 0),
                "sharpe_ratio": float(run.sharpe_ratio or 0),
                "win_rate": float(run.win_rate or 0),
                "profit_loss_ratio": float(run.profit_loss_ratio or 0),
            }
            for run in runs
        ],
        "daily_curves": daily_curves,
    }


def build_industry_exposure(session: Session, run_id: int) -> list[dict]:
    repository = AnalysisRepository(session)
    run = get_run_or_404(session, run_id)
    symbol_map = repository.list_symbols(run.symbols)
    industries = {}
    for symbol in run.symbols:
        industry_name = getattr(symbol_map.get(symbol), "industry", None) or "未分类"
        industries[industry_name] = industries.get(industry_name, 0) + 1
    total = max(sum(industries.values()), 1)
    return [
        {"industry": industry_name, "weight": round(count / total, 4), "count": count}
        for industry_name, count in sorted(industries.items(), key=lambda item: item[1], reverse=True)
    ]


def build_rolling_metric(session: Session, run_id: int, metric: str, window: int) -> list[dict]:
    repository = AnalysisRepository(session)
    daily_rows = repository.list_daily(run_id)
    if not daily_rows:
        return []

    frame = pd.DataFrame(
        [{"trade_date": row.trade_date, "daily_return": float(row.daily_return), "drawdown": float(row.drawdown)} for row in daily_rows]
    )
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])

    if metric == "drawdown":
        frame["value"] = frame["drawdown"].rolling(window=window, min_periods=1).min()
    else:
        rolling_mean = frame["daily_return"].rolling(window=window, min_periods=2).mean()
        rolling_std = frame["daily_return"].rolling(window=window, min_periods=2).std(ddof=0).replace(0, pd.NA)
        frame["value"] = (rolling_mean / rolling_std * (252 ** 0.5)).fillna(0.0)

    return [{"trade_date": row.trade_date.date().isoformat(), "value": float(row.value)} for row in frame.itertuples(index=False)]

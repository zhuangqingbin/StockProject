from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from ..services.tushare_service import DataService
from ..strategies.engine import BacktestEngine, BacktestConfig, BUILTIN_STRATEGIES
from loguru import logger

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


class BacktestRequest(BaseModel):
    ts_code: str
    start_date: str
    end_date: str
    strategy: str
    params: Dict[str, Any] = {}
    initial_capital: float = 1_000_000
    commission_rate: float = 0.0003
    slippage: float = 0.002


@router.get("/list")
async def list_strategies():
    strategies = []
    for key, s in BUILTIN_STRATEGIES.items():
        strategies.append({
            "key": key,
            "name": s["name"],
            "description": s["description"],
            "params": s["params"],
        })
    return {"code": 0, "data": strategies}


@router.post("/backtest")
async def run_backtest(req: BacktestRequest):
    try:
        if req.strategy not in BUILTIN_STRATEGIES:
            raise HTTPException(400, f"Unknown strategy: {req.strategy}")

        strategy_info = BUILTIN_STRATEGIES[req.strategy]

        data = await DataService.get_daily_data(req.ts_code, req.start_date, req.end_date)
        if not data or len(data) < 30:
            raise HTTPException(400, "Insufficient data, need at least 30 trading days")

        config = BacktestConfig(
            initial_capital=req.initial_capital,
            commission_rate=req.commission_rate,
            slippage=req.slippage,
        )
        engine = BacktestEngine(config)

        params = {**req.params, "strategy_name": strategy_info["name"], "ts_code": req.ts_code}
        result = engine.run(data, strategy_info["func"], params)

        return {"code": 0, "data": result.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(500, f"Backtest error: {str(e)}")


class CompareRequest(BaseModel):
    ts_code: str
    start_date: str
    end_date: str
    strategies: list
    initial_capital: float = 1_000_000


@router.post("/compare")
async def compare_strategies(req: CompareRequest):
    try:
        data = await DataService.get_daily_data(req.ts_code, req.start_date, req.end_date)
        if not data or len(data) < 30:
            raise HTTPException(400, "Insufficient data")

        results = []
        engine = BacktestEngine(BacktestConfig(initial_capital=req.initial_capital))

        for s in req.strategies:
            key = s.get("strategy")
            if key not in BUILTIN_STRATEGIES:
                continue
            strategy_info = BUILTIN_STRATEGIES[key]
            params = {**s.get("params", {}), "strategy_name": strategy_info["name"], "ts_code": req.ts_code}
            result = engine.run(data, strategy_info["func"], params)
            results.append(result.to_dict())

        return {"code": 0, "data": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy compare failed: {e}")
        raise HTTPException(500, str(e))

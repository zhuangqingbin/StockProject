from __future__ import annotations

from datetime import datetime

import backtrader as bt
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from apps.stock_backtest.backend.engine.data_feed import build_backtrader_feed, load_symbol_frame
from apps.stock_backtest.backend.engine.metrics import build_daily_snapshots, calculate_performance_metrics
from apps.stock_backtest.backend.engine.result_extractor import PortfolioTimelineAnalyzer, TradeLedgerAnalyzer, extract_backtest_results
from apps.stock_backtest.backend.engine.strategy_loader import resolve_strategy_class
from apps.stock_backtest.backend.infrastructure.database import create_database_engine
from apps.stock_backtest.backend.models.db_models import BacktestDailyModel, BacktestRunModel, BacktestTradeModel, RunStatus, StrategyModel, TradeDirection
from apps.stock_backtest.backend.modules.backtest.diagnostics import append_run_event


def _persist_result(session, run: BacktestRunModel, daily_records: list[dict], trades: list[dict], metrics: dict) -> None:
    session.execute(delete(BacktestTradeModel).where(BacktestTradeModel.run_id == run.id))
    session.execute(delete(BacktestDailyModel).where(BacktestDailyModel.run_id == run.id))

    session.add_all(
        [
            BacktestDailyModel(
                run_id=run.id,
                trade_date=datetime.fromisoformat(record["trade_date"]).date(),
                portfolio_value=record["portfolio_value"],
                cash=record["cash"],
                daily_return=record["daily_return"],
                cumulative_return=record["cumulative_return"],
                drawdown=record["drawdown"],
            )
            for record in daily_records
        ]
    )
    session.add_all(
        [
            BacktestTradeModel(
                run_id=run.id,
                trade_date=datetime.fromisoformat(record["trade_date"]).date(),
                symbol=record["symbol"],
                direction=TradeDirection.BUY if record["direction"] == "buy" else TradeDirection.SELL,
                price=record["price"],
                size=record["size"],
                commission=record["commission"],
                pnl=record["pnl"],
            )
            for record in trades
        ]
    )

    run.status = RunStatus.COMPLETED
    run.progress = 100
    run.error_message = None
    run.total_return = metrics["total_return"]
    run.annual_return = metrics["annual_return"]
    run.max_drawdown = metrics["max_drawdown"]
    run.sharpe_ratio = metrics["sharpe_ratio"]
    run.win_rate = metrics["win_rate"]
    run.profit_loss_ratio = metrics["profit_loss_ratio"]
    run.metrics = metrics
    run.finished_at = datetime.utcnow()


def run_backtest(database_url: str, run_id: int) -> dict:
    engine = create_database_engine(database_url)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    run = None
    try:
        run = session.get(BacktestRunModel, run_id)
        if run is None:
            raise ValueError(f"Unknown run id: {run_id}")
        strategy = session.get(StrategyModel, run.strategy_id)
        if strategy is None:
            raise ValueError(f"Unknown strategy id: {run.strategy_id}")

        run.status = RunStatus.RUNNING
        run.progress = 15
        run.started_at = datetime.utcnow()
        append_run_event(run, "running", "Backtest worker started", progress=15)
        session.commit()

        strategy_class = resolve_strategy_class(
            source_type=strategy.source_type.value,
            template_id=strategy.template_id,
            code=strategy.code,
        )
        feed_ids = list(run.data_feeds or strategy.required_feeds)
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(float(run.initial_cash))
        cerebro.broker.setcommission(commission=float(run.commission_rate))
        cerebro.addstrategy(strategy_class, **{**strategy.default_params, **run.params})
        cerebro.addanalyzer(PortfolioTimelineAnalyzer, _name="timeline")
        cerebro.addanalyzer(TradeLedgerAnalyzer, _name="trade_ledger")

        for symbol in run.symbols:
            frame = load_symbol_frame(
                session=session,
                symbol=symbol,
                start_date=run.start_date,
                end_date=run.end_date,
                feed_ids=feed_ids,
            )
            cerebro.adddata(build_backtrader_feed(frame, symbol))

        run.progress = 55
        append_run_event(
            run,
            "data_loaded",
            "Market data loaded into the backtest engine",
            progress=55,
            metadata={"symbol_count": len(run.symbols), "feed_ids": feed_ids},
        )
        session.commit()

        strategies = cerebro.run()
        strategy_instance = strategies[0]
        raw_equity_curve, raw_trades = extract_backtest_results(strategy_instance)
        daily_records = build_daily_snapshots(raw_equity_curve)
        metrics = calculate_performance_metrics(raw_equity_curve, raw_trades)

        _persist_result(session, run, daily_records, raw_trades, metrics)
        append_run_event(
            run,
            "completed",
            "Backtest finished successfully",
            progress=100,
            metadata={"daily_points": len(daily_records), "trade_count": len(raw_trades)},
        )
        session.commit()
        return {"run_id": run.id, "status": run.status.value, "metrics": metrics, "cache_hit": run.cache_hit, "reused_from_run_id": run.reused_from_run_id}
    except Exception as exc:
        if run is not None:
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            run.progress = 100
            run.finished_at = datetime.utcnow()
            append_run_event(
                run,
                "failed",
                "Backtest execution failed",
                progress=100,
                metadata={"error": str(exc)},
            )
            session.commit()
        raise
    finally:
        session.close()
        engine.dispose()

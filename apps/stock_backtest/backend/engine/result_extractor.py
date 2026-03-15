from __future__ import annotations

import backtrader as bt


class PortfolioTimelineAnalyzer(bt.Analyzer):
    def start(self):
        self._rows = []

    def next(self):
        self._rows.append(
            {
                "trade_date": self.strategy.datetime.date(0).isoformat(),
                "portfolio_value": float(self.strategy.broker.getvalue()),
                "cash": float(self.strategy.broker.get_cash()),
            }
        )

    def get_analysis(self):
        return list(self._rows)


class TradeLedgerAnalyzer(bt.Analyzer):
    def start(self):
        self._rows = []

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        self._rows.append(
            {
                "trade_date": self.strategy.datetime.date(0).isoformat(),
                "symbol": getattr(order.data, "_name", "UNKNOWN"),
                "direction": "buy" if order.isbuy() else "sell",
                "price": float(order.executed.price),
                "size": int(abs(order.executed.size)),
                "commission": float(order.executed.comm),
                "pnl": float(getattr(order.executed, "pnl", 0.0) or 0.0),
            }
        )

    def get_analysis(self):
        return list(self._rows)


def extract_backtest_results(strategy_instance) -> tuple[list[dict], list[dict]]:
    timeline = strategy_instance.analyzers.timeline.get_analysis()
    trades = strategy_instance.analyzers.trade_ledger.get_analysis()
    return timeline, trades

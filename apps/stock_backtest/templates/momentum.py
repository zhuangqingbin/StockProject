import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "momentum",
    "name": "动量策略",
    "description": "定期持有最近涨幅最强的股票。",
    "required_feeds": ["daily_kline", "daily_basic"],
    "parameters": {
        "momentum_period": {"type": "int", "default": 20, "min": 5, "max": 120},
        "top_n": {"type": "int", "default": 1, "min": 1, "max": 10},
        "rebalance_days": {"type": "int", "default": 5, "min": 1, "max": 30},
    },
}


class MomentumRotationStrategy(bt.Strategy):
    params = (("momentum_period", 20), ("top_n", 1), ("rebalance_days", 5))

    def next(self):
        if len(self) < self.params.momentum_period or len(self) % self.params.rebalance_days != 0:
            return

        ranked = sorted(
            self.datas,
            key=lambda data: (data.close[0] / data.close[-self.params.momentum_period]) - 1,
            reverse=True,
        )
        winners = set(ranked[: self.params.top_n])
        target_weight = 0.9 / max(len(winners), 1)

        for data in self.datas:
            if data in winners:
                self.order_target_percent(data=data, target=target_weight)
            elif self.getposition(data):
                self.close(data=data)

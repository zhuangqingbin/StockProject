import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "ma_crossover",
    "name": "均线交叉",
    "description": "短周期均线上穿长周期均线买入，下穿卖出。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "fast_period": {"type": "int", "default": 5, "min": 2, "max": 30},
        "slow_period": {"type": "int", "default": 20, "min": 5, "max": 120},
    },
}


class MovingAverageCrossStrategy(bt.Strategy):
    params = (("fast_period", 5), ("slow_period", 20))

    def __init__(self):
        self._crossovers = {}
        for data in self.datas:
            fast = bt.indicators.SimpleMovingAverage(data.close, period=self.params.fast_period)
            slow = bt.indicators.SimpleMovingAverage(data.close, period=self.params.slow_period)
            self._crossovers[data] = bt.indicators.CrossOver(fast, slow)

    def next(self):
        target_weight = 0.95 / max(len(self.datas), 1)
        for data in self.datas:
            crossover = self._crossovers[data]
            position = self.getposition(data)
            if crossover > 0 and not position:
                self.order_target_percent(data=data, target=target_weight)
            elif crossover < 0 and position:
                self.close(data=data)

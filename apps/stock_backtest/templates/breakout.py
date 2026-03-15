import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "breakout",
    "name": "突破策略",
    "description": "价格突破过去一段时间高点时入场，失守均线离场。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "lookback": {"type": "int", "default": 20, "min": 5, "max": 90},
        "exit_period": {"type": "int", "default": 10, "min": 3, "max": 60},
    },
}


class BreakoutStrategy(bt.Strategy):
    params = (("lookback", 20), ("exit_period", 10))

    def __init__(self):
        self._highs = {data: bt.indicators.Highest(data.high, period=self.params.lookback) for data in self.datas}
        self._exits = {data: bt.indicators.SimpleMovingAverage(data.close, period=self.params.exit_period) for data in self.datas}

    def next(self):
        target_weight = 0.9 / max(len(self.datas), 1)
        for data in self.datas:
            if len(data) < self.params.lookback:
                continue
            position = self.getposition(data)
            if data.close[0] >= self._highs[data][-1] and not position:
                self.order_target_percent(data=data, target=target_weight)
            elif position and data.close[0] < self._exits[data][0]:
                self.close(data=data)

import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "volume_breakout",
    "name": "放量突破",
    "description": "量能超过均值且价格突破区间高点时入场。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "lookback": {"type": "int", "default": 30, "min": 5, "max": 120},
        "volume_period": {"type": "int", "default": 10, "min": 3, "max": 40},
        "volume_multiplier": {"type": "float", "default": 1.8, "min": 1.0, "max": 5.0},
    },
}


class VolumeBreakoutStrategy(bt.Strategy):
    params = (("lookback", 30), ("volume_period", 10), ("volume_multiplier", 1.8))

    def __init__(self):
        self._highs = {data: bt.indicators.Highest(data.high, period=self.params.lookback) for data in self.datas}
        self._volume_sma = {
            data: bt.indicators.SimpleMovingAverage(data.volume, period=self.params.volume_period) for data in self.datas
        }

    def next(self):
        target_weight = 0.9 / max(len(self.datas), 1)
        for data in self.datas:
            if len(data) < self.params.lookback:
                continue
            position = self.getposition(data)
            is_breakout = data.close[0] >= self._highs[data][-1]
            volume_expanded = data.volume[0] >= self._volume_sma[data][0] * self.params.volume_multiplier
            if not position and is_breakout and volume_expanded:
                self.order_target_percent(data=data, target=target_weight)
            elif position and data.close[0] < self._highs[data][-3]:
                self.close(data=data)

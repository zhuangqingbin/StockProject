import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "rsi_rotation",
    "name": "RSI 反转",
    "description": "RSI 超卖区反转入场，回到强势区后离场。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 40},
        "lower_band": {"type": "float", "default": 30.0, "min": 10.0, "max": 45.0},
        "upper_band": {"type": "float", "default": 58.0, "min": 40.0, "max": 85.0},
    },
}


class RSIRotationStrategy(bt.Strategy):
    params = (("rsi_period", 14), ("lower_band", 30.0), ("upper_band", 58.0))

    def __init__(self):
        self._rsi = {data: bt.indicators.RSI(data.close, period=self.params.rsi_period) for data in self.datas}

    def next(self):
        target_weight = 0.9 / max(len(self.datas), 1)
        for data in self.datas:
            rsi = self._rsi[data]
            position = self.getposition(data)
            if not position and rsi[0] <= self.params.lower_band:
                self.order_target_percent(data=data, target=target_weight)
            elif position and rsi[0] >= self.params.upper_band:
                self.close(data=data)

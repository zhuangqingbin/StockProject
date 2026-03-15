import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "atr_trend_following",
    "name": "ATR 趋势跟随",
    "description": "顺着均线趋势持有，用 ATR 动态止损控制回撤。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "trend_period": {"type": "int", "default": 30, "min": 5, "max": 120},
        "atr_period": {"type": "int", "default": 14, "min": 5, "max": 40},
        "atr_multiplier": {"type": "float", "default": 2.5, "min": 1.0, "max": 6.0},
    },
}


class AtrTrendFollowingStrategy(bt.Strategy):
    params = (("trend_period", 30), ("atr_period", 14), ("atr_multiplier", 2.5))

    def __init__(self):
        self._trend = {data: bt.indicators.SimpleMovingAverage(data.close, period=self.params.trend_period) for data in self.datas}
        self._atr = {data: bt.indicators.ATR(data, period=self.params.atr_period) for data in self.datas}
        self._stops = {data: None for data in self.datas}

    def next(self):
        target_weight = 0.92 / max(len(self.datas), 1)
        for data in self.datas:
            position = self.getposition(data)
            atr_value = self._atr[data][0]
            trend_value = self._trend[data][0]
            stop_price = self._stops[data]

            if not position and data.close[0] > trend_value:
                self.order_target_percent(data=data, target=target_weight)
                self._stops[data] = data.close[0] - (atr_value * self.params.atr_multiplier)
                continue

            if not position:
                continue

            self._stops[data] = max(stop_price or 0.0, data.close[0] - (atr_value * self.params.atr_multiplier))
            if data.close[0] <= self._stops[data] or data.close[0] < trend_value:
                self.close(data=data)
                self._stops[data] = None

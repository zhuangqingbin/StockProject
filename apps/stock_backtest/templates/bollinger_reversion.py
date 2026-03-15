import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "bollinger_reversion",
    "name": "布林回补",
    "description": "价格跌破下轨后分批回补，中轨止盈。",
    "required_feeds": ["daily_kline"],
    "parameters": {
        "period": {"type": "int", "default": 18, "min": 5, "max": 60},
        "devfactor": {"type": "float", "default": 2.2, "min": 1.0, "max": 4.0},
    },
}


class BollingerReversionStrategy(bt.Strategy):
    params = (("period", 18), ("devfactor", 2.2))

    def __init__(self):
        self._bands = {
            data: bt.indicators.BollingerBands(data.close, period=self.params.period, devfactor=self.params.devfactor)
            for data in self.datas
        }

    def next(self):
        target_weight = 0.85 / max(len(self.datas), 1)
        for data in self.datas:
            bands = self._bands[data]
            position = self.getposition(data)
            if not position and data.close[0] <= bands.bot[0]:
                self.order_target_percent(data=data, target=target_weight)
            elif position and data.close[0] >= bands.mid[0]:
                self.close(data=data)

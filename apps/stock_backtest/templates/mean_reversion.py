import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "mean_reversion",
    "name": "均值回归",
    "description": "价格跌出布林下轨后回归中轨时卖出。",
    "required_feeds": ["daily_kline", "daily_basic"],
    "parameters": {
        "period": {"type": "int", "default": 20, "min": 5, "max": 90},
        "devfactor": {"type": "float", "default": 2.0, "min": 1.0, "max": 4.0},
    },
}


class MeanReversionStrategy(bt.Strategy):
    params = (("period", 20), ("devfactor", 2.0))

    def __init__(self):
        self._bands = {
            data: bt.indicators.BollingerBands(data.close, period=self.params.period, devfactor=self.params.devfactor)
            for data in self.datas
        }

    def next(self):
        target_weight = 0.9 / max(len(self.datas), 1)
        for data in self.datas:
            bands = self._bands[data]
            position = self.getposition(data)
            if data.close[0] < bands.bot[0] and not position:
                self.order_target_percent(data=data, target=target_weight)
            elif position and data.close[0] >= bands.mid[0]:
                self.close(data=data)

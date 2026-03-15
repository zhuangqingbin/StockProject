import backtrader as bt


TEMPLATE_METADATA = {
    "template_id": "money_flow",
    "name": "资金流向",
    "description": "主力净流入显著放大时建仓，均线走弱时离场。",
    "required_feeds": ["daily_kline", "moneyflow"],
    "parameters": {
        "flow_threshold": {"type": "float", "default": 5000.0, "min": 0, "max": 1000000},
        "exit_period": {"type": "int", "default": 10, "min": 3, "max": 60},
    },
}


class MoneyFlowStrategy(bt.Strategy):
    params = (("flow_threshold", 5000.0), ("exit_period", 10))

    def __init__(self):
        self._exit_lines = {data: bt.indicators.SimpleMovingAverage(data.close, period=self.params.exit_period) for data in self.datas}

    def next(self):
        target_weight = 0.9 / max(len(self.datas), 1)
        for data in self.datas:
            flow_value = getattr(data, "net_mf_amount", [0.0])[0]
            position = self.getposition(data)
            if flow_value >= self.params.flow_threshold and not position:
                self.order_target_percent(data=data, target=target_weight)
            elif position and data.close[0] < self._exit_lines[data][0]:
                self.close(data=data)

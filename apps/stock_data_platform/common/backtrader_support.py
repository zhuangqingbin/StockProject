try:
    import backtrader as bt
except ImportError:  # pragma: no cover - optional dependency for backtesting helpers
    bt = None


if bt is not None:
    class AShareCommission(bt.CommInfoBase):
        params = (
            ("commission", 0.0003),
            ("stamp_duty", 0.0005),
            ("min_commission", 5.0),
            ("transfer_fee", 0.0),
            ("stocklike", True),
            ("commtype", bt.CommInfoBase.COMM_PERC),
        )

        def _getcommission(self, size, price, pseudoexec):
            value = abs(size) * price
            broker_comm = max(value * self.p.commission, self.p.min_commission) if value > 0 else 0.0
            stamp = value * self.p.stamp_duty if size < 0 else 0.0
            transfer = value * self.p.transfer_fee if self.p.transfer_fee > 0 else 0.0
            return broker_comm + stamp + transfer


    class AShareSizer(bt.Sizer):
        params = (
            ("lot_size", 100),
            ("cash_keep", 0.00),
        )

        def _getsizing(self, comminfo, cash, data, isbuy):
            price = data.close[0]
            if isbuy:
                budget = cash * (1 - self.p.cash_keep)
                if price <= 0:
                    return 0
                lots = int((budget / price) // self.p.lot_size)
                return max(lots * self.p.lot_size, 0)
            pos = self.broker.getposition(data)
            return int(pos.size)


else:
    class AShareCommission:  # pragma: no cover - helper placeholder when backtrader is absent
        def __init__(self, *args, **kwargs):
            raise ImportError("backtrader is required to use AShareCommission")


    class AShareSizer:  # pragma: no cover - helper placeholder when backtrader is absent
        def __init__(self, *args, **kwargs):
            raise ImportError("backtrader is required to use AShareSizer")

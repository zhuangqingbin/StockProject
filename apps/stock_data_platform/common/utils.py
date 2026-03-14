import math
import os
import pickle
import time
from contextlib import contextmanager
from typing import Union

from shared.stock_core.db import create_mysql_engine

try:
    import backtrader as bt
except ImportError:  # pragma: no cover - optional dependency for backtesting helpers
    bt = None


@contextmanager
def timer(name):
    start = time.time()
    yield
    print(f"[{name}] done in {time.time() - start:.2f} s")


def save(obj, file_path):
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        print(f"[{dir_name}] Not Exists.\n\t Create New Folder ...")
        os.makedirs(dir_name)
    with open(file_path, "wb") as file_obj:
        pickle.dump(obj, file_obj)
    print("Save successfully.")


def load(file_path):
    with open(file_path, "rb") as file_obj:
        return pickle.load(file_obj)


def datetime2str(value):
    return f"{value.year}{value.month:0>2}{value.day:0>2}"


def get_trade_cal(start_date, end_date):
    from DataFetch import TradeCalFetch

    fetcher = TradeCalFetch()
    calendar_df = fetcher.fetch(start_date=start_date, end_date=end_date)
    return list(calendar_df[calendar_df.is_open == 1]["cal_date"])


def get_pv(pmt, rate, n):
    q = 1 / (1 + rate)
    return pmt * (1 - q ** n) / (1 - q)


def get_pmt(pv, rate, n):
    q = 1 / (1 + rate)
    return pv * (1 - q) / (1 - q ** n)


def get_rate(pv, pmt, n):
    low_rate, high_rate = 0.0, 10.0
    while low_rate < high_rate:
        mid_rate = (low_rate + high_rate) / 2
        if abs(get_pv(pmt, mid_rate, n) - pv) < 1e-5:
            return mid_rate
        if get_pv(pmt, mid_rate, n) > pv:
            low_rate = mid_rate
        else:
            high_rate = mid_rate
    return low_rate


def get_n(pv, pmt, rate):
    q = 1 / (1 + rate)
    return math.log(1 - pv / pmt * (1 - q), q)


def get_engine():
    return create_mysql_engine()


def code_add_suffix(ts_code: Union[str, int]) -> str:
    if isinstance(ts_code, int):
        code = str(ts_code)
    elif isinstance(ts_code, str):
        code = ts_code
    else:
        raise ValueError(f"ts_code({ts_code}) must be int or str.")

    if code.endswith((".SH", ".SZ", ".BJ")):
        return code
    if code.startswith(("60", "68")):
        return f"{code}.SH"
    if code.startswith(("00", "30")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    raise ValueError(f"ts_code({ts_code}) must start with 60/68/00/30/4/8")


def get_prev_trade_days(date: str, n: int):
    import akshare as ak
    import pandas as pd

    trade_dates_df = ak.tool_trade_date_hist_sina()
    trade_dates_df["trade_date"] = pd.to_datetime(trade_dates_df["trade_date"])
    target_date = pd.to_datetime(date)
    before_target = trade_dates_df[trade_dates_df["trade_date"] < target_date]
    return before_target["trade_date"].tail(n).dt.strftime("%Y-%m-%d").tolist()


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

"""
指数数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=95
"""
import pandas as pd

from .BaseClass import BaseDataFetch


BI_TRACKED_INDEX_CODES = (
    "000001.SH",
    "399001.SZ",
    "399006.SZ",
    "000688.SH",
    "000300.SH",
)


class IndexDailyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=95
    指数日线行情, 120积分
        获取指数每日行情
    API params:
        ts_code: 指数代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "trade_date",
            "close", "open", "high", "low",
            "pre_close", "change", "pct_chg",
            "vol", "amount"
        ]
        fields = ",".join(self.fields)
        ts_code = kwargs.get("ts_code")

        if ts_code:
            return self.client.call("index_daily", fields=fields, **kwargs)

        frames: list[pd.DataFrame] = []
        for index_code in BI_TRACKED_INDEX_CODES:
            frame = self.client.call(
                "index_daily",
                fields=fields,
                ts_code=index_code,
                **kwargs,
            )
            if frame is not None and not frame.empty:
                frames.append(frame)

        if not frames:
            return pd.DataFrame(columns=self.fields)

        return pd.concat(frames, ignore_index=True)

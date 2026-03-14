def get_trade_cal(start_date, end_date):
    from apps.stock_data_platform.DataFetch import TradeCalFetch

    fetcher = TradeCalFetch()
    calendar_df = fetcher.fetch(start_date=start_date, end_date=end_date)
    return list(calendar_df[calendar_df.is_open == 1]["cal_date"])


def get_prev_trade_days(date: str, n: int):
    import akshare as ak
    import pandas as pd

    trade_dates_df = ak.tool_trade_date_hist_sina()
    trade_dates_df["trade_date"] = pd.to_datetime(trade_dates_df["trade_date"])
    target_date = pd.to_datetime(date)
    before_target = trade_dates_df[trade_dates_df["trade_date"] < target_date]
    return before_target["trade_date"].tail(n).dt.strftime("%Y-%m-%d").tolist()

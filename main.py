from BaseClass.stock_basic import *

# stock_basic = StockBasicFetch()
# stock_basic.fetch_data("股票基础信息")
# stock_basic.summary_data()
#
# stock_trade_cal = TradeCalFetch()
# stock_trade_cal.fetch_data("股票交易", start_date='20220801', end_date='20220808')
# stock_trade_cal.summary_data()

stock_namechange = NameChangeFetch()
stock_namechange.fetch_data("股票曾用名", ts_code ="600848.SH", start_date='20220801', end_date='20240808')
stock_namechange.summary_data()
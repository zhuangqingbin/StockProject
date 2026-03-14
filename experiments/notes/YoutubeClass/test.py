import datetime
import backtrader as bt
import pandas as pd
import matplotlib

class MyStrategy(bt.Strategy):
    pass

# 1 Create a cerebro
cerebro = bt.Cerebro()

# 2. Add data feed
# 2.1 Create a data feed
dataframe = pd.read_csv("AAPL.csv")
dataframe['Date'] = pd.to_datetime(dataframe['Date'])
dataframe.set_index("Date", inplace = True)
dataframe["openinterest"] = 0
brf_daily = bt.feeds.PandasData(
    dataname = dataframe,
    fromdate = datetime.datetime(2021,12,31),
    todate = datetime.datetime(2022,12,1)
)
brf_daily = bt.feeds.GenericCSVData(
    dataname = 'AAPL.csv',
    fromdate = datetime.datetime(2021,12,31),
    todate = datetime.datetime(2022,12,1),
    nullvalue = 0,
    dtformat = "%Y-%m-%d",
    datetime = 0, # 第一列
    open = 1, # 第二列
    high=2,
    low=3,
    close=4,
    volume=6,
    openinterest=-1 # 不存在这个数据
)

# 2.2 Add the DataStore Feed to Cerebro
cerebro.adddata(brf_daily)

# 3 Add strategy
cerebro.addstrategy(MyStrategy)

# 4 run
cerebro.run()

# 5 Plot result
cerebro.plot()
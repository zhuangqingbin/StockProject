from DataFetch.stock_basic import StockBasicFetch

s = StockBasicFetch()
s.fetch_data("ff")
print(s.data)
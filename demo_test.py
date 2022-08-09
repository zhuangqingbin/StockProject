print("f")
# pip install --target=/Users/jimmy/.conda/envs/StockProject/lib/python3.8/site-packages
import tushare as ts


pro = ts.pro_api('64ce1845b91d06f579525db6e53d497b1c513174331f5509320f4bd5')
df = pro.tmt_twincome(item='8')

import tushare as ts
import os
import sys

CURR_FILE_PATH = os.path.realpath(__file__)
CONFIG_FILE_PATH = os.path.join(CURR_FILE_PATH, '../../common')
sys.path.append(CONFIG_FILE_PATH)
from common.config import TOKEN
print(TOKEN)
pro = ts.pro_api(TOKEN)

#获取单日全部股票数据
df = pro.moneyflow(trade_date='20220815')

df.head(2)
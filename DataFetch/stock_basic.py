import os
import sys
from abc import abstractmethod

CURR_FILE_PATH = os.path.realpath(__file__)
BASE_CLASS_FILE_PATH = os.path.join(CURR_FILE_PATH, '../BaseClass')

sys.path.append(BASE_CLASS_FILE_PATH)

from BaseClass.BaseDataFetch import BaseDataFetch
import tushare as ts

class StockBasicFetch(BaseDataFetch):
    """
    基础信息
        获取基础信息数据，包括股票代码、名称、上市日期、退市日期等
    """
    def read_data(self):
        self.data = self.pro.stock_basic(exchange='', list_status='L',
                                         fields='ts_code,symbol,name,area,industry,market,list_date')

class TradeCalFetch(BaseDataFetch):
    """
    交易日历
        获取各大交易所交易日历数据,默认提取的是上交所
    """
    def read_data(self, start_date, end_date):
        self.data = self.pro.trade_cal(exchange='', start_date=start_date, end_date=end_date)

class NameChangeFetch(BaseDataFetch):
    """
    股票曾用名
        历史名称变更记录
    """
    def read_data(self, ts_code, start_date, end_date):
        self.data = self.pro.namechange(ts_code=ts_code,
                                        start_date=start_date, end_date=end_date)

class StockCompanyFetch(BaseDataFetch):
    """
    上市公司基本信息
        获取上市公司基础信息
    """
    def read_data(self, ts_code = None, exchange = None):
        self.data = self.pro.stock_company(ts_code = ts_code, exchange = exchange)

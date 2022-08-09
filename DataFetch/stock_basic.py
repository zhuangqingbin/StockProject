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

    """
    def read_data(self):
        self.data = self.pro.stock_basic(exchange='', list_status='L',
                                         fields='ts_code,symbol,name,area,industry,market,list_date')

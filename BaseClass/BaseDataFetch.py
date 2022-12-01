import os
import sys
from abc import abstractmethod

CURR_FILE_PATH = os.path.realpath(__file__)
CONFIG_FILE_PATH = os.path.join(CURR_FILE_PATH, '../common')
sys.path.append(CONFIG_FILE_PATH)


from common.utils import timer
from common.config import TOKEN
import tushare as ts

class BaseDataFetch:
    def __init__(self):
        self.pro = ts.pro_api(TOKEN)
        self.data = None

    @abstractmethod
    def read_data(self):
        pass

    def fetch_data(self, name = "", **kwargs):
        with timer("获取: " + name):
            self.read_data(**kwargs)

    def summary_data(self):
        if self.data is not None:
            print("Shape: " + str(self.data.shape))
            print("Cols: " + str(self.data.columns))
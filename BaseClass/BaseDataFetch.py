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

    @abstractmethod
    def read_data(self):
        pass

    def fetch_data(self, name = ""):
        with timer(name):
            self.read_data()
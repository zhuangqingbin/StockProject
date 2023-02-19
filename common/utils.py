from contextlib import contextmanager
import time
import chinese_calendar
import datetime, os
import pickle
import tushare as ts
from config import TOKEN

pro = ts.pro_api(TOKEN)

@contextmanager
def timer(name):
    start = time.time()
    yield
    print(f'[{name}] done in {time.time() - start:.2f} s')

def save(obj, file_path):
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        print(f'[{dir_name}] Not Exists. \n\t Create New Folder ...')
        os.makedirs(dir_name)
        print(f'Save sucessfully.')
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)
        
def load(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def datetime2str(d):
    return "{}{:0>2}{:0>2}".format(d.year, d.month, d.day)

def get_trade_cal(start_date, end_date):
    # exchange/cal_date/is_open/pretrade_date
    cal_df = pro.trade_cal(exchange='SSE', start_date=start_date,
                  end_date=end_date)
    return list(cal_df[cal_df.is_open == 1]['cal_date'])
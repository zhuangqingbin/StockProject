import math
import os
import pickle
import sys
import time
from contextlib import contextmanager
import pymysql
from sqlalchemy import create_engine
from .config import *


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
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)
    print(f'Save sucessfully.')
        
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


# pv: 现值; pmt" 每期缴纳; rate: 利率; n: 期数; fv: 终值 = (1+rate)**n
# FV = 终值 PV (1+rate)
# q = 1 / (1 + rate) ; pmt * (1 - q ** n) / (1 - q) = pv
def get_pv(pmt, rate, n):
    q = 1 / (1 + rate)
    return pmt * (1 - q ** n) / (1 - q)

def get_pmt(pv, rate, n):
    q = 1 / (1 + rate)
    return pv * (1 - q) / (1 - q ** n)

def get_rate(pv, pmt, n):
    low_rate, high_rate = 0.0, 10.0
    while low_rate < high_rate:
        mid_rate = (low_rate + high_rate) / 2
        if abs(get_pv(pmt, mid_rate, n) - pv) < 1e-5:
            return mid_rate
        elif get_pv(pmt, mid_rate, n) > pv:
            low_rate = mid_rate
        else:
            high_rate = mid_rate
def get_n(pv, pmt, rate):
    q = 1 / (1 + rate)
    return math.log(1 - pv / pmt * (1 - q), q)


def get_engine():
    """
    demo:
        engine = get_engine()
        query = ""
        df1 = pd.read_sql(query, engine)
    """
    conn_str = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    return create_engine(conn_str)

def create_table_daily_kline(engine):
    with engine.connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_kline (
            ts_code VARCHAR(10),
            trade_date DATE,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            change_val FLOAT,
            pct_chg FLOAT,
            vol FLOAT,
            amount FLOAT,
            PRIMARY KEY (ts_code, trade_date)
        );
        """)

def code_add_suffix(ts_code: str) -> str:
    if type(ts_code) == int:
        code = str(code)
    elif type(ts_code) == str:
        pass
    else:
        raise ValueError(f"ts_code({ts_code}) must be int or str.")
    if ts_code.startswith(('60', '68')):
        return ts_code + '.SH'
    elif ts_code.startswith(('00', '30')):
        return ts_code + '.SZ'
    elif ts_code.startswith(('4', '8')):
        return ts_code + '.BJ'
    else:
        raise ValueError(f"ts_code({ts_code}) must start with 60/68/00/30/4/8")

        
def get_prev_trade_days(date: str, n: int):
    """
    获取某个日期之前的 n 个 A 股交易日（不含当天）
    
    :param date: 日期字符串，格式 '2024-05-14'
    :param n: 向前取 n 个交易日
    :return: n 个交易日构成的 list
    """
    # 获取从远古到指定日期的所有交易日
    trade_dates_df = ak.tool_trade_date_hist_sina()
    trade_dates_df['trade_date'] = pd.to_datetime(trade_dates_df['trade_date'])
    
    target_date = pd.to_datetime(date)
    
    # 筛选出小于目标日期的日期
    before_target = trade_dates_df[trade_dates_df['trade_date'] < target_date]
    
    # 取最后 n 个
    result = before_target['trade_date'].tail(n).dt.strftime('%Y-%m-%d').tolist()
    
    return result
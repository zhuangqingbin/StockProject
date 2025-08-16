# StockProject
## Content
```
.
|-- Backtrader
|-- BaseClass
|   |-- BaseDataFetch.py
|   |-- Test.py
|   `-- __init__.py
|-- DataFetch
|   `-- stock_basic.py
|-- DataStore
|   |-- Important
|   |-- Local
|   `-- Temp
|-- Note
|   |-- Debug
|   `-- YoutubeClass
|-- README.md
|-- Work
|-- common
|   |-- AutoEmail.py
|   |-- IndustryTop.yaml
|   |-- config.py
|   `-- utils.py
|-- demo_test.py
|-- draft.py
|-- main.py
|-- requirements.txt
`-- requirements2.txt
```

- DataStore: data storage directory
  - Important: will be uploaded to github
    - `df_sw2021_industry_info.pkl`: 
      - description: SWS 2021 Industry Classification (31 first-level classifications, 134 second-level classifications, 346 third-level classifications)
      - code in `common/code_repository.py` **get_sw_ind_list**
  - Local: will not be uploaded to github
  - Temp: temporary storage

## Download package from third-party source
- create env
  - conda create -n env39 python=3.9
  - conda create -n env37 python=3.7
  - conda create -n env36 python=3.6
    - Recommend to use python3.6 because matplotlib (need by cerebro.plot)should be 3.2.2
  - show virtual env in jupyter notebook
    - conda install nb_conda
    - pip install -r requirements.txt
    - jupyter notebook
      - add nbextensions
        - install: pip install jupyter_contrib_nbextensions
        - setup: jupyter contrib nbextension install --user
        - Open the jupyter notebook; Go to Nbextensions tab


- get directory path
```python
import os
print(os.path) # xxx/anaconda3/lib/python3.8/posixpath.py
# pip install --target=xxx/anaconda3/lib/python3.8/site-packages PACKAGE
```

## Mysql read and write
### Install Mysql on MacOS
1. install mysql
```bash
brew install mysql
```
2. start mysql service
```bash
brew services start mysql
```
3. set root password
```bash
mysql_secure_installation
```

### Create database & table
1. enter mysql
```bash
mysql -u root -p
```
2. create database
```bash
CREATE DATABASE stock_data;
USE stock_data;
```
3.create table
```bash

CREATE TABLE daily_kline (
    ts_code    VARCHAR(10) NOT NULL,
    trade_date CHAR(8)     NOT NULL,           -- 存 YYYYMMDD
    open       FLOAT,
    high       FLOAT,
    low        FLOAT,
    close      FLOAT,
    pre_close  FLOAT,
    `change`   FLOAT,
    pct_chg    FLOAT,
    vol        FLOAT,
    amount     FLOAT,
    PRIMARY KEY (ts_code, trade_date),
    CHECK (trade_date REGEXP '^[0-9]{8}$')     -- MySQL 8.0+ 才会真正生效
);
```

### Read and write Mysql with python
1. enter mysql]()
```python
import tushare as ts
import pandas as pd
from sqlalchemy import create_engine

# 设置 TuShare token
ts.set_token('你的token')
pro = ts.pro_api()

# 获取某一天的数据
date = '20240510'
df = pro.daily(trade_date=date)

# 数据清洗
df = df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']]
df['trade_date'] = pd.to_datetime(df['trade_date'])

# 创建 MySQL 引擎（替换密码）
engine = create_engine("mysql+pymysql://root:你的密码@localhost/stock_data?charset=utf8")

# 写入数据库（如果已存在则替换该行）
df.to_sql('daily_kline', engine, if_exists='append', index=False, method='multi')


# 读取某只股票最近30天数据
ts_code = '600519.SH'
query = f"""
SELECT * FROM daily_kline
WHERE ts_code = '{ts_code}'
ORDER BY trade_date DESC
LIMIT 30
"""
df = pd.read_sql(query, engine)
print(df.head())

```

## Backtrader感悟
- 统一用self.datas[X]的方式比较好,X就是adddata的顺序
- self.data(即self.datas[0])本质也是一个line,和定义的指标一样,假设定义了一个指标A(lines有B和C),访问B和C分别为self.A.lines.B其中lines可以省略,访问data中的close也可以self.datas[0].lines.close,但是通常省略为self.datas[0].close
- get(ago=0,size=0), 返回截止包含到ago位置的size数组
- ()defaly操作, self.data.close(-1) → 一条“移位后的 line”（上一根 close，仍是 line，可在 \_\_init__ 里与其它 line 组合生成新 line）;self.data.close[-1] → 一个即时数值（上一根的具体数）。只能在 next() 里安全使用；在 \_\_init__ 里用会把逻辑“固化”或直接越界
- order.status有order.Completed, order.Canceled, order.Rejected, rder.Submitted, order.Accepted
```python
class TestStrategy(bt.Strategy):
    def __init__(self):
        # To keep track of pending orders and buy price/commission
        self.order = None 
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None  # 只有这些结束状态才清空
    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
# submit和accept仍然不设置为None， 因为这个时候还没真正完成
# 回测时：下单 → Submitted → Accepted → Completed
# 实盘：下单 → Submitted → Accepted → （等待几秒/几分钟） → Completed
```
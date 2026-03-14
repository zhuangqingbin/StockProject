# Stock BI 数据可视化平台 - 功能需求文档 v2.6

## 1. 项目概述

### 1.1 目标
构建一个全面的 A 股数据可视化平台，支持：
- 市场全景概览（当日数据展示在页面顶部）
- 多维度数据分析（行情、资金、龙虎榜、财务等）
- 自然语言 Chat 交互查询
- 历史数据趋势分析
- **实时数据更新**（WebSocket 推送）
- **数据一致性保障**（多表日期校验）

### 1.2 数据源
基于 [TuShare Pro](https://tushare.pro/) API，用户拥有 5000+ 积分，可调用绝大部分高级接口。

> ⚠️ **注意**: 港股日线行情 `hk_daily` 需要单独购买权限（1000元/年），非积分制度，本平台暂不支持。

---

## 2. 数据表设计（基于 TuShare API 和 DataFetch 模块）

> 所有表遵循统一格式：字段对齐、带 COMMENT 注释、参考 [TuShare 文档](https://tushare.pro/document/2)

### 2.1 核心行情数据

#### `daily_kline` A股日K线（已有）
```sql
-- TuShare 接口: pro.daily()
-- 文档: https://tushare.pro/document/2?doc_id=27
-- DataFetch: StockDailyFetch
CREATE TABLE IF NOT EXISTS daily_kline (
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    open        FLOAT                  COMMENT '开盘价',
    high        FLOAT                  COMMENT '最高价',
    low         FLOAT                  COMMENT '最低价',
    close       FLOAT                  COMMENT '收盘价',
    pre_close   FLOAT                  COMMENT '昨收价(除权价)',
    `change`    FLOAT                  COMMENT '涨跌额',
    pct_chg     FLOAT                  COMMENT '涨跌幅(%)(基于除权后的昨收计算)',
    vol         FLOAT                  COMMENT '成交量(手)',
    amount      FLOAT                  COMMENT '成交额(千元)',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_pct (trade_date, pct_chg),
    INDEX idx_date_amount (trade_date, amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='A股日K线数据';
```

#### `daily_basic` 每日指标
```sql
-- TuShare 接口: pro.daily_basic()
-- 文档: https://tushare.pro/document/2?doc_id=32
-- DataFetch: StockDailyBasicFetch
CREATE TABLE IF NOT EXISTS daily_basic (
    ts_code         VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    trade_date      VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    close           FLOAT                  COMMENT '当日收盘价',
    turnover_rate   FLOAT                  COMMENT '换手率(%)',
    turnover_rate_f FLOAT                  COMMENT '换手率(自由流通股)',
    volume_ratio    FLOAT                  COMMENT '量比',
    pe              FLOAT                  COMMENT '市盈率(总市值/净利润,亏损为空)',
    pe_ttm          FLOAT                  COMMENT '市盈率TTM(亏损为空)',
    pb              FLOAT                  COMMENT '市净率(总市值/净资产)',
    ps              FLOAT                  COMMENT '市销率',
    ps_ttm          FLOAT                  COMMENT '市销率TTM',
    dv_ratio        FLOAT                  COMMENT '股息率(%)',
    dv_ttm          FLOAT                  COMMENT '股息率TTM(%)',
    total_share     FLOAT                  COMMENT '总股本(万股)',
    float_share     FLOAT                  COMMENT '流通股本(万股)',
    free_share      FLOAT                  COMMENT '自由流通股本(万股)',
    total_mv        FLOAT                  COMMENT '总市值(万元)',
    circ_mv         FLOAT                  COMMENT '流通市值(万元)',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_pe (trade_date, pe),
    INDEX idx_date_turnover (trade_date, turnover_rate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日指标数据';
```

### 2.2 股票基础信息

#### `stock_basic` 股票列表
```sql
-- TuShare 接口: pro.stock_basic()
-- 文档: https://tushare.pro/document/2?doc_id=25
-- DataFetch: StockBasicFetch
CREATE TABLE IF NOT EXISTS stock_basic (
    ts_code     VARCHAR(10)   NOT NULL  COMMENT 'TS代码',
    symbol      VARCHAR(10)             COMMENT '股票代码',
    name        VARCHAR(50)             COMMENT '股票名称',
    area        VARCHAR(20)             COMMENT '地域',
    industry    VARCHAR(50)             COMMENT '所属行业',
    market      VARCHAR(10)             COMMENT '市场类别(主板/创业板/科创板/CDR/北交所)',
    exchange    VARCHAR(10)             COMMENT '交易所代码(SSE/SZSE/BSE)',
    is_hs       VARCHAR(5)              COMMENT '是否沪深港通(N/H/S)',
    list_date   VARCHAR(8)              COMMENT '上市日期(YYYYMMDD)',
    PRIMARY KEY (ts_code),
    INDEX idx_market (market),
    INDEX idx_industry (industry),
    INDEX idx_exchange (exchange)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基础信息';
```

#### `trade_cal` 交易日历
```sql
-- TuShare 接口: pro.trade_cal()
-- 文档: https://tushare.pro/document/2?doc_id=26
-- DataFetch: TradeCalFetch
CREATE TABLE IF NOT EXISTS trade_cal (
    exchange    VARCHAR(10)  NOT NULL  COMMENT '交易所(SSE/SZSE/CFFEX等)',
    cal_date    VARCHAR(8)   NOT NULL  COMMENT '日期(YYYYMMDD)',
    is_open     VARCHAR(1)             COMMENT '是否交易(0休市/1交易)',
    PRIMARY KEY (exchange, cal_date),
    INDEX idx_cal_date (cal_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易日历';
```

#### `stock_company` 上市公司基本信息
```sql
-- TuShare 接口: pro.stock_company()
-- 文档: https://tushare.pro/document/2?doc_id=112
-- DataFetch: StockCompanyFetch
CREATE TABLE IF NOT EXISTS stock_company (
    ts_code         VARCHAR(10)   NOT NULL  COMMENT 'TS代码',
    com_name        VARCHAR(100)            COMMENT '公司名称',
    reg_capital     FLOAT                   COMMENT '注册资本(万元)',
    province        VARCHAR(20)             COMMENT '省份',
    city            VARCHAR(30)             COMMENT '城市',
    employees       INT                     COMMENT '员工人数',
    main_business   TEXT                    COMMENT '主要业务',
    business_scope  TEXT                    COMMENT '经营范围',
    PRIMARY KEY (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='上市公司基本信息';
```

### 2.3 资金流向数据

#### `moneyflow` 个股资金流向
```sql
-- TuShare 接口: pro.moneyflow()
-- 文档: https://tushare.pro/document/2?doc_id=170
-- DataFetch: MoneyFlowFetch
CREATE TABLE IF NOT EXISTS moneyflow (
    ts_code         VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    trade_date      VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    buy_sm_vol      FLOAT                  COMMENT '小单买入量(手)',
    buy_sm_amount   FLOAT                  COMMENT '小单买入金额(万元)',
    sell_sm_vol     FLOAT                  COMMENT '小单卖出量(手)',
    sell_sm_amount  FLOAT                  COMMENT '小单卖出金额(万元)',
    buy_md_vol      FLOAT                  COMMENT '中单买入量(手)',
    buy_md_amount   FLOAT                  COMMENT '中单买入金额(万元)',
    sell_md_vol     FLOAT                  COMMENT '中单卖出量(手)',
    sell_md_amount  FLOAT                  COMMENT '中单卖出金额(万元)',
    buy_lg_vol      FLOAT                  COMMENT '大单买入量(手)',
    buy_lg_amount   FLOAT                  COMMENT '大单买入金额(万元)',
    sell_lg_vol     FLOAT                  COMMENT '大单卖出量(手)',
    sell_lg_amount  FLOAT                  COMMENT '大单卖出金额(万元)',
    buy_elg_vol     FLOAT                  COMMENT '特大单买入量(手)',
    buy_elg_amount  FLOAT                  COMMENT '特大单买入金额(万元)',
    sell_elg_vol    FLOAT                  COMMENT '特大单卖出量(手)',
    sell_elg_amount FLOAT                  COMMENT '特大单卖出金额(万元)',
    net_mf_vol      FLOAT                  COMMENT '净流入量(手)',
    net_mf_amount   FLOAT                  COMMENT '净流入额(万元)',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_netmf (trade_date, net_mf_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个股资金流向';
```

#### `moneyflow_hsgt` 沪深港通资金流向
```sql
-- TuShare 接口: pro.moneyflow_hsgt()
-- 文档: https://tushare.pro/document/2?doc_id=47
-- DataFetch: MoneyFlowHSGTFetch
CREATE TABLE IF NOT EXISTS moneyflow_hsgt (
    trade_date   VARCHAR(8)  NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ggt_ss       FLOAT                 COMMENT '港股通(沪)净流入(百万)',
    ggt_sz       FLOAT                 COMMENT '港股通(深)净流入(百万)',
    hgt          FLOAT                 COMMENT '沪股通净流入(百万)',
    sgt          FLOAT                 COMMENT '深股通净流入(百万)',
    north_money  FLOAT                 COMMENT '北向资金净流入(百万)',
    south_money  FLOAT                 COMMENT '南向资金净流入(百万)',
    PRIMARY KEY (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='沪深港通资金流向';
```

#### `hsgt_top10` 沪深港通十大成交股
```sql
-- TuShare 接口: pro.hsgt_top10()
-- 文档: https://tushare.pro/document/2?doc_id=48
-- DataFetch: HSGTTop10Fetch
CREATE TABLE IF NOT EXISTS hsgt_top10 (
    trade_date   VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code      VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    name         VARCHAR(50)            COMMENT '股票名称',
    close        FLOAT                  COMMENT '收盘价',
    `change`     FLOAT                  COMMENT '涨跌额',
    `rank`       INT                    COMMENT '资金排名',
    market_type  VARCHAR(5)             COMMENT '市场类型(1沪股通/2深股通/3港股通沪/4港股通深)',
    amount       FLOAT                  COMMENT '成交金额(百万)',
    net_amount   FLOAT                  COMMENT '净买入金额(百万)',
    buy          FLOAT                  COMMENT '买入金额(百万)',
    sell         FLOAT                  COMMENT '卖出金额(百万)',
    PRIMARY KEY (trade_date, ts_code, market_type),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='沪深港通十大成交股';
```

### 2.4 龙虎榜数据

#### `top_list` 龙虎榜每日明细
```sql
-- TuShare 接口: pro.top_list()
-- 文档: https://tushare.pro/document/2?doc_id=106
-- DataFetch: TopListFetch
CREATE TABLE IF NOT EXISTS top_list (
    trade_date    VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code       VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    name          VARCHAR(50)            COMMENT '股票名称',
    close         FLOAT                  COMMENT '收盘价',
    pct_change    FLOAT                  COMMENT '涨跌幅(%)',
    turnover_rate FLOAT                  COMMENT '换手率(%)',
    amount        FLOAT                  COMMENT '总成交额(万)',
    l_sell        FLOAT                  COMMENT '龙虎榜卖出额(万)',
    l_buy         FLOAT                  COMMENT '龙虎榜买入额(万)',
    l_amount      FLOAT                  COMMENT '龙虎榜成交额(万)',
    net_amount    FLOAT                  COMMENT '龙虎榜净买入额(万)',
    net_rate      FLOAT                  COMMENT '龙虎榜净买入占比(%)',
    amount_rate   FLOAT                  COMMENT '龙虎榜成交额占比(%)',
    float_values  FLOAT                  COMMENT '当日流通市值(万)',
    reason        VARCHAR(200)           COMMENT '上榜原因',
    PRIMARY KEY (trade_date, ts_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_netamt (trade_date, net_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='龙虎榜每日明细';
```

#### `top_inst` 龙虎榜机构交易明细
```sql
-- TuShare 接口: pro.top_inst()
-- 文档: https://tushare.pro/document/2?doc_id=107
-- DataFetch: TopInstFetch
CREATE TABLE IF NOT EXISTS top_inst (
    trade_date  VARCHAR(8)    NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code     VARCHAR(10)   NOT NULL  COMMENT '股票代码',
    exalter     VARCHAR(200)  NOT NULL  COMMENT '营业部名称',
    buy         FLOAT                   COMMENT '买入额(万)',
    buy_rate    FLOAT                   COMMENT '买入占总成交比例(%)',
    sell        FLOAT                   COMMENT '卖出额(万)',
    sell_rate   FLOAT                   COMMENT '卖出占总成交比例(%)',
    net_buy     FLOAT                   COMMENT '净买入额(万)',
    side        VARCHAR(10)             COMMENT '买卖方向(BUY/SELL)',
    PRIMARY KEY (trade_date, ts_code, exalter(100)),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='龙虎榜机构交易明细';
```

### 2.5 涨跌停数据

#### `limit_list` 涨跌停榜单
```sql
-- TuShare 接口: pro.limit_list_d()
-- 文档: https://tushare.pro/document/2?doc_id=198
-- DataFetch: LimitListFetch
CREATE TABLE IF NOT EXISTS limit_list (
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    name        VARCHAR(50)            COMMENT '股票名称',
    close       FLOAT                  COMMENT '收盘价',
    pct_chg     FLOAT                  COMMENT '涨跌幅(%)',
    amp         FLOAT                  COMMENT '振幅(%)',
    fc_ratio    FLOAT                  COMMENT '封单金额/流通市值',
    fl_ratio    FLOAT                  COMMENT '封单手数/流通股本',
    fd_amount   FLOAT                  COMMENT '封单金额(万)',
    first_time  VARCHAR(10)            COMMENT '首次涨跌停时间(HH:MM:SS)',
    last_time   VARCHAR(10)            COMMENT '最后涨跌停时间(HH:MM:SS)',
    open_times  INT                    COMMENT '打开次数',
    strth       FLOAT                  COMMENT '涨跌停强度',
    `limit`     VARCHAR(5)             COMMENT '涨跌停类型(U涨停/D跌停/Z炸板)',
    PRIMARY KEY (trade_date, ts_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_limit (trade_date, `limit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='涨跌停榜单';
```

#### `stk_limit` 每日涨跌停价格
```sql
-- TuShare 接口: pro.stk_limit()
-- 文档: https://tushare.pro/document/2?doc_id=183
-- DataFetch: StkLimitFetch
CREATE TABLE IF NOT EXISTS stk_limit (
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    pre_close   FLOAT                  COMMENT '昨日收盘价',
    up_limit    FLOAT                  COMMENT '涨停价',
    down_limit  FLOAT                  COMMENT '跌停价',
    PRIMARY KEY (trade_date, ts_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日涨跌停价格';
```

### 2.6 指数数据

#### `index_daily` 指数日线行情
```sql
-- TuShare 接口: pro.index_daily()
-- 文档: https://tushare.pro/document/2?doc_id=95
-- DataFetch: IndexDailyFetch
-- 常用: 000001.SH上证 399001.SZ深证 399006.SZ创业板 000688.SH科创50 000300.SH沪深300
CREATE TABLE IF NOT EXISTS index_daily (
    ts_code     VARCHAR(15)  NOT NULL  COMMENT '指数代码',
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    close       FLOAT                  COMMENT '收盘点位',
    open        FLOAT                  COMMENT '开盘点位',
    high        FLOAT                  COMMENT '最高点位',
    low         FLOAT                  COMMENT '最低点位',
    pre_close   FLOAT                  COMMENT '昨收点位',
    `change`    FLOAT                  COMMENT '涨跌点',
    pct_chg     FLOAT                  COMMENT '涨跌幅(%)',
    vol         FLOAT                  COMMENT '成交量(手)',
    amount      FLOAT                  COMMENT '成交额(千元)',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数日线行情';
```

#### `index_basic` 指数基本信息
```sql
-- TuShare 接口: pro.index_basic()
-- 文档: https://tushare.pro/document/2?doc_id=94
-- DataFetch: IndexBasicFetch
CREATE TABLE IF NOT EXISTS index_basic (
    ts_code     VARCHAR(15)   NOT NULL  COMMENT '指数代码',
    name        VARCHAR(100)            COMMENT '简称',
    fullname    VARCHAR(200)            COMMENT '指数全称',
    market      VARCHAR(20)             COMMENT '市场(MSCI/CSI/SSE/SZSE/CICC/SW等)',
    publisher   VARCHAR(50)             COMMENT '发布方',
    index_type  VARCHAR(20)             COMMENT '指数类型',
    category    VARCHAR(20)             COMMENT '指数类别',
    base_date   VARCHAR(8)              COMMENT '基期',
    base_point  FLOAT                   COMMENT '基点',
    list_date   VARCHAR(8)              COMMENT '发布日期',
    weight_rule VARCHAR(50)             COMMENT '加权方式',
    `desc`      TEXT                    COMMENT '描述',
    exp_date    VARCHAR(8)              COMMENT '终止日期',
    PRIMARY KEY (ts_code),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数基本信息';
```

#### `index_sw_daily` 申万行业指数日线
```sql
-- TuShare 接口: pro.sw_daily()
-- 文档: https://tushare.pro/document/2?doc_id=298
-- DataFetch: SWIndexDailyFetch
CREATE TABLE IF NOT EXISTS index_sw_daily (
    ts_code     VARCHAR(15)  NOT NULL  COMMENT '申万行业指数代码(如801010.SI)',
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    name        VARCHAR(50)            COMMENT '行业名称',
    open        FLOAT                  COMMENT '开盘点位',
    low         FLOAT                  COMMENT '最低点位',
    high        FLOAT                  COMMENT '最高点位',
    close       FLOAT                  COMMENT '收盘点位',
    `change`    FLOAT                  COMMENT '涨跌点',
    pct_change  FLOAT                  COMMENT '涨跌幅(%)',
    vol         FLOAT                  COMMENT '成交量(手)',
    amount      FLOAT                  COMMENT '成交额(千元)',
    pe          FLOAT                  COMMENT '市盈率',
    pb          FLOAT                  COMMENT '市净率',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_date_pct (trade_date, pct_change)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申万行业指数日线';
```

#### `index_classify` 申万行业分类
```sql
-- TuShare 接口: pro.index_classify()
-- 文档: https://tushare.pro/document/2?doc_id=181
-- DataFetch: IndexClassifyFetch
CREATE TABLE IF NOT EXISTS index_classify (
    index_code     VARCHAR(15)  NOT NULL  COMMENT '指数代码',
    industry_name  VARCHAR(50)            COMMENT '行业名称',
    level          VARCHAR(5)             COMMENT '行业级别(L1/L2/L3)',
    industry_code  VARCHAR(20)            COMMENT '行业代码',
    is_pub         VARCHAR(5)             COMMENT '是否发布指数',
    parent_code    VARCHAR(20)            COMMENT '父级代码',
    PRIMARY KEY (index_code),
    INDEX idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申万行业分类';
```

#### `index_member` 申万行业成分股
```sql
-- TuShare 接口: pro.index_member()
-- 文档: https://tushare.pro/document/2?doc_id=182
-- DataFetch: IndexMemberFetch
CREATE TABLE IF NOT EXISTS index_member (
    index_code  VARCHAR(15)  NOT NULL  COMMENT '指数代码',
    index_name  VARCHAR(50)            COMMENT '指数名称',
    con_code    VARCHAR(10)  NOT NULL  COMMENT '成分股代码',
    con_name    VARCHAR(50)            COMMENT '成分股名称',
    in_date     VARCHAR(8)             COMMENT '纳入日期',
    out_date    VARCHAR(8)             COMMENT '剔除日期',
    is_new      VARCHAR(5)             COMMENT '是否最新(Y/N)',
    PRIMARY KEY (index_code, con_code),
    INDEX idx_con_code (con_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申万行业成分股';
```

### 2.7 港股数据

> ⚠️ **注意**: `hk_daily` (港股日线行情) 需要**单独购买权限** (1000元/年)，不是积分制度。
> 详情参考: https://tushare.pro/document/1?doc_id=290

#### `hk_daily` 港股日线行情 (需单独购买权限)
```sql
-- ⚠️ 此接口需要单独购买权限 (1000元/年)，DDL仅供参考
-- TuShare 接口: pro.hk_daily()
-- 文档: https://tushare.pro/document/2?doc_id=192
-- 如已购买权限，取消下方注释创建表

-- CREATE TABLE IF NOT EXISTS hk_daily (
--     ts_code     VARCHAR(15)  NOT NULL  COMMENT '港股代码(如00700.HK)',
--     trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
--     open        FLOAT                  COMMENT '开盘价',
--     high        FLOAT                  COMMENT '最高价',
--     low         FLOAT                  COMMENT '最低价',
--     close       FLOAT                  COMMENT '收盘价',
--     pre_close   FLOAT                  COMMENT '昨收价',
--     `change`    FLOAT                  COMMENT '涨跌额',
--     pct_chg     FLOAT                  COMMENT '涨跌幅(%)',
--     vol         FLOAT                  COMMENT '成交量(手)',
--     amount      FLOAT                  COMMENT '成交额(千港元)',
--     PRIMARY KEY (ts_code, trade_date),
--     INDEX idx_trade_date (trade_date)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='港股日线行情';
```

#### `hk_basic` 港股基础信息 (2000积分)
```sql
-- TuShare 接口: pro.hk_basic()
-- 文档: https://tushare.pro/document/2?doc_id=189
-- DataFetch: HKBasicFetch
CREATE TABLE IF NOT EXISTS hk_basic (
    ts_code      VARCHAR(15)   NOT NULL  COMMENT 'TS代码',
    name         VARCHAR(100)            COMMENT '股票名称',
    fullname     VARCHAR(200)            COMMENT '公司全称',
    enname       VARCHAR(200)            COMMENT '英文名称',
    cn_spell     VARCHAR(50)             COMMENT '拼音',
    market       VARCHAR(10)             COMMENT '市场类别(主板/创业板)',
    list_status  VARCHAR(5)              COMMENT '上市状态(L上市/D退市/P暂停)',
    list_date    VARCHAR(8)              COMMENT '上市日期',
    delist_date  VARCHAR(8)              COMMENT '退市日期',
    trade_unit   INT                     COMMENT '交易单位(股)',
    isin         VARCHAR(20)             COMMENT 'ISIN代码',
    curr_type    VARCHAR(10)             COMMENT '交易货币',
    PRIMARY KEY (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='港股基础信息';
```

#### `ggt_daily` 港股通每日成交统计(市场汇总)
```sql
-- TuShare 接口: pro.ggt_daily()
-- 文档: https://tushare.pro/document/2?doc_id=196
-- DataFetch: GGTDailyFetch
-- 注意: 这是市场整体统计,不是单股数据
CREATE TABLE IF NOT EXISTS ggt_daily (
    trade_date   VARCHAR(8)  NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    buy_amount   FLOAT                 COMMENT '买入成交金额(亿元)',
    buy_volume   FLOAT                 COMMENT '买入成交笔数(万笔)',
    sell_amount  FLOAT                 COMMENT '卖出成交金额(亿元)',
    sell_volume  FLOAT                 COMMENT '卖出成交笔数(万笔)',
    PRIMARY KEY (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='港股通每日成交统计(市场汇总)';
```

### 2.8 融资融券数据

#### `margin` 融资融券交易汇总
```sql
-- TuShare 接口: pro.margin()
-- 文档: https://tushare.pro/document/2?doc_id=58
-- DataFetch: MarginFetch
CREATE TABLE IF NOT EXISTS margin (
    trade_date   VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    exchange_id  VARCHAR(10)  NOT NULL  COMMENT '交易所(SSE/SZSE)',
    rzye         FLOAT                  COMMENT '融资余额(元)',
    rzmre        FLOAT                  COMMENT '融资买入额(元)',
    rzche        FLOAT                  COMMENT '融资偿还额(元)',
    rqye         FLOAT                  COMMENT '融券余额(元)',
    rqmcl        FLOAT                  COMMENT '融券卖出量(股)',
    rzrqye       FLOAT                  COMMENT '融资融券余额(元)',
    rqyl         FLOAT                  COMMENT '融券余量(股)',
    PRIMARY KEY (trade_date, exchange_id),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='融资融券交易汇总';
```

#### `margin_detail` 融资融券交易明细
```sql
-- TuShare 接口: pro.margin_detail()
-- 文档: https://tushare.pro/document/2?doc_id=59
-- DataFetch: MarginDetailFetch
CREATE TABLE IF NOT EXISTS margin_detail (
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    name        VARCHAR(50)            COMMENT '股票名称',
    rzye        FLOAT                  COMMENT '融资余额(元)',
    rqye        FLOAT                  COMMENT '融券余额(元)',
    rzmre       FLOAT                  COMMENT '融资买入额(元)',
    rqyl        FLOAT                  COMMENT '融券余量(股)',
    rzche       FLOAT                  COMMENT '融资偿还额(元)',
    rqchl       FLOAT                  COMMENT '融券偿还量(股)',
    rqmcl       FLOAT                  COMMENT '融券卖出量(股)',
    rzrqye      FLOAT                  COMMENT '融资融券余额(元)',
    PRIMARY KEY (trade_date, ts_code),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='融资融券交易明细';
```

### 2.9 财务数据

#### `income` 利润表
```sql
-- TuShare 接口: pro.income() / pro.income_vip()
-- 文档: https://tushare.pro/document/2?doc_id=33
-- DataFetch: IncomeFetch / IncomeVipFetch
CREATE TABLE IF NOT EXISTS income (
    ts_code         VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date        VARCHAR(8)             COMMENT '公告日期',
    end_date        VARCHAR(8)   NOT NULL  COMMENT '报告期(YYYYMMDD)',
    report_type     VARCHAR(5)   NOT NULL  COMMENT '报告类型(1合并/2单季/3调整合并/4调整单季)',
    comp_type       VARCHAR(5)             COMMENT '公司类型(1一般/2银行/3保险/4证券)',
    basic_eps       FLOAT                  COMMENT '基本每股收益(元)',
    diluted_eps     FLOAT                  COMMENT '稀释每股收益(元)',
    total_revenue   FLOAT                  COMMENT '营业总收入(元)',
    revenue         FLOAT                  COMMENT '营业收入(元)',
    total_cogs      FLOAT                  COMMENT '营业总成本(元)',
    operate_profit  FLOAT                  COMMENT '营业利润(元)',
    total_profit    FLOAT                  COMMENT '利润总额(元)',
    n_income        FLOAT                  COMMENT '净利润(元)',
    n_income_attr_p FLOAT                  COMMENT '归属于母公司净利润(元)',
    ebit            FLOAT                  COMMENT '息税前利润(元)',
    ebitda          FLOAT                  COMMENT '息税折旧摊销前利润(元)',
    PRIMARY KEY (ts_code, end_date, report_type),
    INDEX idx_ann_date (ann_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='利润表';
```

#### `balancesheet` 资产负债表
```sql
-- TuShare 接口: pro.balancesheet()
-- 文档: https://tushare.pro/document/2?doc_id=36
-- DataFetch: BalanceSheetFetch
CREATE TABLE IF NOT EXISTS balancesheet (
    ts_code                     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date                    VARCHAR(8)             COMMENT '公告日期',
    end_date                    VARCHAR(8)   NOT NULL  COMMENT '报告期',
    report_type                 VARCHAR(5)   NOT NULL  COMMENT '报告类型',
    comp_type                   VARCHAR(5)             COMMENT '公司类型',
    total_assets                FLOAT                  COMMENT '资产总计(元)',
    total_liab                  FLOAT                  COMMENT '负债合计(元)',
    total_hldr_eqy_exc_min_int  FLOAT                  COMMENT '股东权益合计(不含少数)(元)',
    total_hldr_eqy_inc_min_int  FLOAT                  COMMENT '股东权益合计(含少数)(元)',
    total_cur_assets            FLOAT                  COMMENT '流动资产合计(元)',
    total_nca                   FLOAT                  COMMENT '非流动资产合计(元)',
    total_cur_liab              FLOAT                  COMMENT '流动负债合计(元)',
    total_ncl                   FLOAT                  COMMENT '非流动负债合计(元)',
    accounts_receiv             FLOAT                  COMMENT '应收账款(元)',
    inventories                 FLOAT                  COMMENT '存货(元)',
    money_cap                   FLOAT                  COMMENT '货币资金(元)',
    PRIMARY KEY (ts_code, end_date, report_type),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产负债表';
```

#### `cashflow` 现金流量表
```sql
-- TuShare 接口: pro.cashflow()
-- 文档: https://tushare.pro/document/2?doc_id=44
-- DataFetch: CashFlowFetch
CREATE TABLE IF NOT EXISTS cashflow (
    ts_code               VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date              VARCHAR(8)             COMMENT '公告日期',
    end_date              VARCHAR(8)   NOT NULL  COMMENT '报告期',
    report_type           VARCHAR(5)   NOT NULL  COMMENT '报告类型',
    comp_type             VARCHAR(5)             COMMENT '公司类型',
    net_profit            FLOAT                  COMMENT '净利润(元)',
    n_cashflow_act        FLOAT                  COMMENT '经营活动现金流量净额(元)',
    n_cashflow_inv_act    FLOAT                  COMMENT '投资活动现金流量净额(元)',
    n_cash_flows_fnc_act  FLOAT                  COMMENT '筹资活动现金流量净额(元)',
    c_cash_equ_end_period FLOAT                  COMMENT '期末现金及现金等价物(元)',
    c_cash_equ_beg_period FLOAT                  COMMENT '期初现金及现金等价物(元)',
    PRIMARY KEY (ts_code, end_date, report_type),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='现金流量表';
```

#### `fina_indicator` 财务指标
```sql
-- TuShare 接口: pro.fina_indicator()
-- 文档: https://tushare.pro/document/2?doc_id=79
-- DataFetch: FinaIndicatorFetch
CREATE TABLE IF NOT EXISTS fina_indicator (
    ts_code          VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date         VARCHAR(8)             COMMENT '公告日期',
    end_date         VARCHAR(8)   NOT NULL  COMMENT '报告期',
    eps              FLOAT                  COMMENT '基本每股收益(元)',
    dt_eps           FLOAT                  COMMENT '稀释每股收益(元)',
    bps              FLOAT                  COMMENT '每股净资产(元)',
    roe              FLOAT                  COMMENT '净资产收益率(%)',
    roe_dt           FLOAT                  COMMENT '净资产收益率(扣非)(%)',
    roa              FLOAT                  COMMENT '总资产净利率(%)',
    current_ratio    FLOAT                  COMMENT '流动比率',
    quick_ratio      FLOAT                  COMMENT '速动比率',
    gross_margin     FLOAT                  COMMENT '销售毛利率(%)',
    netprofit_margin FLOAT                  COMMENT '销售净利率(%)',
    debt_to_assets   FLOAT                  COMMENT '资产负债率(%)',
    op_yoy           FLOAT                  COMMENT '营业利润同比(%)',
    profit_yoy       FLOAT                  COMMENT '净利润同比(%)',
    PRIMARY KEY (ts_code, end_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务指标';

### 2.10 高级数据 (5000+积分)

#### `hk_hold` 沪深股通持股明细
```sql
-- TuShare 接口: pro.hk_hold()
-- 文档: https://tushare.pro/document/2?doc_id=188
-- DataFetch: HKHoldFetch
CREATE TABLE IF NOT EXISTS hk_hold (
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    name        VARCHAR(50)            COMMENT '股票名称',
    vol         FLOAT                  COMMENT '持股数量(股)',
    ratio       FLOAT                  COMMENT '持股占比(%)',
    exchange    VARCHAR(5)             COMMENT '类型(SH沪股通/SZ深股通)',
    PRIMARY KEY (trade_date, ts_code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='沪深股通持股明细';
```

#### `cyq_perf` 每日筹码及胜率
```sql
-- TuShare 接口: pro.cyq_perf()
-- 文档: https://tushare.pro/document/2?doc_id=293
-- DataFetch: CyqPerfFetch
CREATE TABLE IF NOT EXISTS cyq_perf (
    ts_code      VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    trade_date   VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    his_low      FLOAT                  COMMENT '历史最低价',
    his_high     FLOAT                  COMMENT '历史最高价',
    cost_5pct    FLOAT                  COMMENT '5%成本价',
    cost_15pct   FLOAT                  COMMENT '15%成本价',
    cost_50pct   FLOAT                  COMMENT '50%成本价',
    cost_85pct   FLOAT                  COMMENT '85%成本价',
    cost_95pct   FLOAT                  COMMENT '95%成本价',
    weight_avg   FLOAT                  COMMENT '加权平均成本',
    winner_rate  FLOAT                  COMMENT '胜率(%)',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日筹码及胜率';
```

#### `stk_factor` 股票技术面因子
```sql
-- TuShare 接口: pro.stk_factor_pro()
-- 文档: https://tushare.pro/document/2?doc_id=294
-- DataFetch: StkFactorFetch
CREATE TABLE IF NOT EXISTS stk_factor (
    ts_code     VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    trade_date  VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    close       FLOAT                  COMMENT '收盘价',
    open        FLOAT                  COMMENT '开盘价',
    high        FLOAT                  COMMENT '最高价',
    low         FLOAT                  COMMENT '最低价',
    vol         FLOAT                  COMMENT '成交量(手)',
    amount      FLOAT                  COMMENT '成交额(千元)',
    macd_dif    FLOAT                  COMMENT 'MACD_DIF',
    macd_dea    FLOAT                  COMMENT 'MACD_DEA',
    macd        FLOAT                  COMMENT 'MACD',
    kdj_k       FLOAT                  COMMENT 'KDJ_K',
    kdj_d       FLOAT                  COMMENT 'KDJ_D',
    kdj_j       FLOAT                  COMMENT 'KDJ_J',
    rsi_6       FLOAT                  COMMENT 'RSI_6',
    rsi_12      FLOAT                  COMMENT 'RSI_12',
    rsi_24      FLOAT                  COMMENT 'RSI_24',
    boll_upper  FLOAT                  COMMENT 'BOLL上轨',
    boll_mid    FLOAT                  COMMENT 'BOLL中轨',
    boll_lower  FLOAT                  COMMENT 'BOLL下轨',
    cci         FLOAT                  COMMENT 'CCI指标',
    PRIMARY KEY (ts_code, trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票技术面因子';
```

#### `block_trade` 大宗交易
```sql
-- TuShare 接口: pro.block_trade()
-- 文档: https://tushare.pro/document/2?doc_id=152
-- DataFetch: BlockTradeFetch
CREATE TABLE IF NOT EXISTS block_trade (
    ts_code     VARCHAR(10)   NOT NULL  COMMENT '股票代码',
    trade_date  VARCHAR(8)    NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    name        VARCHAR(50)             COMMENT '股票名称',
    price       FLOAT                   COMMENT '成交价',
    vol         FLOAT                   COMMENT '成交量(万股)',
    amount      FLOAT                   COMMENT '成交金额(万元)',
    buyer       VARCHAR(100)            COMMENT '买方营业部',
    seller      VARCHAR(100)            COMMENT '卖方营业部',
    PRIMARY KEY (trade_date, ts_code, buyer(50), seller(50)),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='大宗交易';
```

#### `stk_holdernumber` 股东人数
```sql
-- TuShare 接口: pro.stk_holdernumber()
-- 文档: https://tushare.pro/document/2?doc_id=166
-- DataFetch: StkHolderNumberFetch
CREATE TABLE IF NOT EXISTS stk_holdernumber (
    ts_code           VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date          VARCHAR(8)             COMMENT '公告日期',
    end_date          VARCHAR(8)   NOT NULL  COMMENT '报告期',
    holder_num        INT                    COMMENT '股东总数',
    holder_num_change INT                    COMMENT '股东人数变化',
    holder_num_ratio  FLOAT                  COMMENT '股东人数变化比例(%)',
    holder_num_pct    FLOAT                  COMMENT '较上期变动幅度(%)',
    PRIMARY KEY (ts_code, end_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股东人数';
```

#### `top10_holders` 前十大股东
```sql
-- TuShare 接口: pro.top10_holders()
-- 文档: https://tushare.pro/document/2?doc_id=61
-- DataFetch: Top10HoldersFetch
CREATE TABLE IF NOT EXISTS top10_holders (
    ts_code      VARCHAR(10)   NOT NULL  COMMENT '股票代码',
    ann_date     VARCHAR(8)              COMMENT '公告日期',
    end_date     VARCHAR(8)    NOT NULL  COMMENT '报告期',
    holder_name  VARCHAR(200)  NOT NULL  COMMENT '股东名称',
    hold_amount  FLOAT                   COMMENT '持股数量(股)',
    hold_ratio   FLOAT                   COMMENT '持股比例(%)',
    hold_change  FLOAT                   COMMENT '持股变化(股)',
    holder_type  VARCHAR(20)             COMMENT '股东类型',
    PRIMARY KEY (ts_code, end_date, holder_name(100)),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='前十大股东';
```

#### `top10_floatholders` 前十大流通股东
```sql
-- TuShare 接口: pro.top10_floatholders()
-- 文档: https://tushare.pro/document/2?doc_id=62
-- DataFetch: Top10FloatHoldersFetch
CREATE TABLE IF NOT EXISTS top10_floatholders (
    ts_code      VARCHAR(10)   NOT NULL  COMMENT '股票代码',
    ann_date     VARCHAR(8)              COMMENT '公告日期',
    end_date     VARCHAR(8)    NOT NULL  COMMENT '报告期',
    holder_name  VARCHAR(200)  NOT NULL  COMMENT '股东名称',
    hold_amount  FLOAT                   COMMENT '持股数量(股)',
    hold_ratio   FLOAT                   COMMENT '持股比例(%)',
    hold_change  FLOAT                   COMMENT '持股变化(股)',
    holder_type  VARCHAR(20)             COMMENT '股东类型',
    PRIMARY KEY (ts_code, end_date, holder_name(100)),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='前十大流通股东';
```

#### `dividend` 分红送股
```sql
-- TuShare 接口: pro.dividend()
-- 文档: https://tushare.pro/document/2?doc_id=103
-- DataFetch: DividendFetch
CREATE TABLE IF NOT EXISTS dividend (
    ts_code       VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    ann_date      VARCHAR(8)             COMMENT '公告日期',
    end_date      VARCHAR(8)   NOT NULL  COMMENT '分红年度',
    div_proc      VARCHAR(20)            COMMENT '实施进度',
    stk_div       FLOAT                  COMMENT '每股送股比例',
    stk_bo_rate   FLOAT                  COMMENT '每股转增比例',
    stk_co_rate   FLOAT                  COMMENT '每股配股比例',
    cash_div      FLOAT                  COMMENT '每股分红(税后)',
    cash_div_tax  FLOAT                  COMMENT '每股分红(税前)',
    record_date   VARCHAR(8)             COMMENT '股权登记日',
    ex_date       VARCHAR(8)             COMMENT '除权除息日',
    pay_date      VARCHAR(8)             COMMENT '派息日',
    PRIMARY KEY (ts_code, end_date),
    INDEX idx_end_date (end_date),
    INDEX idx_ex_date (ex_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分红送股';
```

#### `share_float` 限售股解禁
```sql
-- TuShare 接口: pro.share_float()
-- 文档: https://tushare.pro/document/2?doc_id=160
-- DataFetch: ShareFloatFetch
CREATE TABLE IF NOT EXISTS share_float (
    ts_code      VARCHAR(10)   NOT NULL  COMMENT '股票代码',
    ann_date     VARCHAR(8)              COMMENT '公告日期',
    float_date   VARCHAR(8)    NOT NULL  COMMENT '解禁日期',
    float_share  FLOAT                   COMMENT '解禁数量(万股)',
    float_ratio  FLOAT                   COMMENT '解禁比例(%)',
    holder_name  VARCHAR(200)            COMMENT '股东名称',
    share_type   VARCHAR(50)             COMMENT '股份类型',
    PRIMARY KEY (ts_code, float_date, holder_name(100)),
    INDEX idx_float_date (float_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='限售股解禁';
```

#### `pledge_stat` 股权质押统计
```sql
-- TuShare 接口: pro.pledge_stat()
-- 文档: https://tushare.pro/document/2?doc_id=110
-- DataFetch: PledgeStatFetch
CREATE TABLE IF NOT EXISTS pledge_stat (
    ts_code       VARCHAR(10)  NOT NULL  COMMENT '股票代码',
    end_date      VARCHAR(8)   NOT NULL  COMMENT '截止日期',
    pledge_count  INT                    COMMENT '质押次数',
    unrest_pledge FLOAT                  COMMENT '无限售股质押数量(万股)',
    rest_pledge   FLOAT                  COMMENT '限售股份质押数量(万股)',
    total_share   FLOAT                  COMMENT '总股本(万股)',
    pledge_ratio  FLOAT                  COMMENT '质押比例(%)',
    PRIMARY KEY (ts_code, end_date),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股权质押统计';
```

### 2.11 预计算/缓存表（性能优化）

#### `market_daily_summary` 每日市场汇总（预计算）
```sql
-- 预计算表：存储每日市场聚合数据，加速前端查询
-- 由后端定时任务生成，支持秒级响应
CREATE TABLE IF NOT EXISTS market_daily_summary (
    trade_date          VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
    -- 基础统计
    total_stocks        INT                    COMMENT '股票总数',
    up_count            INT                    COMMENT '上涨家数',
    down_count          INT                    COMMENT '下跌家数',
    flat_count          INT                    COMMENT '平盘家数',
    limit_up            INT                    COMMENT '涨停家数',
    limit_down          INT                    COMMENT '跌停家数',
    avg_pct_chg         FLOAT                  COMMENT '平均涨跌幅(%)',
    total_amount        FLOAT                  COMMENT '总成交额(亿元)',
    total_vol           FLOAT                  COMMENT '总成交量(亿手)',
    -- JSON存储的聚合数据
    sector_stats        JSON                   COMMENT '板块统计(按交易所分)',
    industry_stats      JSON                   COMMENT '行业统计(申万一级)',
    pct_distribution    JSON                   COMMENT '涨跌幅分布',
    top_gainers         JSON                   COMMENT '涨幅Top20',
    top_losers          JSON                   COMMENT '跌幅Top20',
    top_amount          JSON                   COMMENT '成交额Top20',
    top_turnover        JSON                   COMMENT '换手率Top20',
    -- 北向资金
    north_money         JSON                   COMMENT '北向资金数据',
    -- 龙虎榜
    top_list_summary    JSON                   COMMENT '龙虎榜汇总',
    -- 涨跌停详情
    limit_stats         JSON                   COMMENT '涨跌停统计(首板/连板等)',
    -- 行业排名
    industry_ranking    JSON                   COMMENT '申万行业涨跌排名',
    -- 大盘指数
    index_data          JSON                   COMMENT '主要指数数据',
    -- 时间戳
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日市场汇总(预计算)';
```

---

## 3. 可视化功能设计

### 3.1 页面顶部：当日数据日期显示

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Stock BI    📅 数据日期: 2025-01-31 (周五)    [刷新] [设置]           │
│              最后更新: 16:30:00                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 市场全景概览卡片（Dashboard Cards）

| 卡片 | 数据 | TuShare 接口 |
|------|------|--------------|
| 大盘指数 | 上证/深证/创业板指 涨跌幅 | `index_daily` |
| 涨跌统计 | 上涨/下跌/平盘家数 | `daily_kline` 聚合 |
| 涨跌停 | 涨停/跌停/炸板家数 | `limit_list_d` |
| 成交额 | 沪深总成交额，环比变化 | `daily_kline` 聚合 |
| 北向资金 | 今日净流入，近5日累计 | `moneyflow_hsgt` |
| 融资余额 | 两市融资余额，增减 | `margin` |

### 3.3 主图表类型（扩展）

#### 3.3.1 板块热力图（Treemap）
- **数据源**: `stock_basic` + `daily_kline` + `industry_sw`
- **维度**: 申万一级行业 / 交易所板块
- **颜色**: 涨跌幅映射
- **面积**: 成交额 / 流通市值

#### 3.3.2 资金流向图（新增重点）
- **北向资金趋势**: `moneyflow_hsgt` 近30日走势
- **个股主力净流入排行**: `moneyflow` 大单净流入 Top 20
- **行业资金流向**: 按行业聚合 `moneyflow`
- **沪深港通十大成交股**: `hsgt_top10`

#### 3.3.3 龙虎榜分析（新增重点）
- **今日龙虎榜股票**: `top_list` 当日数据
- **机构席位买卖**: `top_inst` 机构净买入排行
- **游资营业部活跃度**: 按营业部聚合
- **连续上榜股票**: 近N日连续上榜

#### 3.3.4 涨跌停分析（新增重点）
- **涨停板统计**: 首板/2连板/3连板+
- **涨停时间分布**: 早盘/午盘/尾盘首封
- **炸板率统计**: 曾涨停但收盘未封住
- **跌停分析**: 跌停原因（ST、退市风险等）

#### 3.3.5 行业轮动分析
- **申万行业涨跌排行**: `index_sw_daily` 今日排名
- **行业资金流向**: 行业净流入排行
- **行业强弱对比**: 近5日 vs 今日表现气泡图
- **行业估值分布**: PE/PB 分位数

#### 3.3.6 指数分析
- **大盘K线**: 上证/深证/创业板/科创50
- **指数对比**: 多指数走势叠加
- **市场宽度**: 上涨家数占比趋势
- **成交量能**: 指数成交额趋势

#### 3.3.7 港股联动（新增）
- **港股主要指数**: 恒生指数、恒生科技
- **AH溢价**: AH股溢价指数
- **南向资金**: 港股通净流入趋势
- **港股热门股**: 港股通成交活跃股

#### 3.3.8 融资融券分析（新增）
- **两融余额趋势**: 近30日走势
- **融资净买入排行**: 个股融资净买入 Top 20
- **融券卖出排行**: 融券做空比例高的股票

### 3.4 辅助图表

| 图表 | 说明 | 数据源 |
|------|------|--------|
| 成交额趋势 | 近30日沪深成交额 | `daily_kline` 聚合 |
| 涨停趋势 | 每日涨停家数变化 | `limit_list_d` |
| 北向资金趋势 | 近30日北向净流入 | `moneyflow_hsgt` |
| 市场情绪指标 | 涨跌比、涨停数、换手率 | 综合计算 |
| 估值分布 | PE/PB 分布直方图 | `daily_basic` |

---

## 4. Chat 命令扩展

### 4.1 新增支持的查询类型

| 意图 | 示例命令 | 数据源 |
|------|----------|--------|
| 资金流向 | "今天北向资金流入多少" | `moneyflow_hsgt` |
| 主力资金 | "主力净流入最多的股票" | `moneyflow` |
| 龙虎榜 | "今天龙虎榜有哪些股票" | `top_list` |
| 机构动向 | "机构今天买了什么" | `top_inst` |
| 涨停分析 | "今天有多少连板" | `limit_list_d` |
| 行业排名 | "哪个行业今天最强" | `index_sw_daily` |
| 港股 | "恒生科技今天涨跌" | ⚠️ `hk_daily`需单独购买权限 |
| 融资融券 | "融资余额变化" | `margin` |
| 估值 | "PE最低的股票" | `daily_basic` |
| 换手率 | "换手率最高的股票" | `daily_basic` |

### 4.2 对话示例扩展

```
User: 今天北向资金流入多少？

AI: 📈 2025-01-31 北向资金流向

沪股通: +45.2 亿元
深股通: +32.8 亿元
合计净流入: +78.0 亿元

近5日累计: +156.3 亿元
本月累计: +423.5 亿元

[已生成北向资金趋势图]

---

User: 今天龙虎榜有哪些股票？

AI: 🐉 2025-01-31 龙虎榜

共 35 只股票上榜，主要原因：
- 涨幅偏离值达7%: 18 只
- 振幅达15%: 8 只
- 换手率达20%: 9 只

机构净买入 Top 3:
1. 中芯国际 +2.3亿
2. 宁德时代 +1.8亿
3. 比亚迪 +1.2亿

[已生成龙虎榜明细表]

---

User: 今天有多少连板股？

AI: 🔥 2025-01-31 连板统计

首板: 45 只
2连板: 12 只
3连板: 5 只
4连板+: 2 只

最高连板:
- XX股份 (6连板) - 半导体概念
- YY科技 (5连板) - AI概念

炸板率: 18.5% (今日曾涨停45只，收盘封住37只)

[已生成涨停梯队图]
```

---

## 5. 数据更新机制

### 5.1 定时任务规划

| 数据表 | 更新频率 | 更新时间 | TuShare 接口 |
|--------|----------|----------|--------------|
| daily_kline | 每日 | 16:00 | `daily` |
| daily_basic | 每日 | 16:30 | `daily_basic` |
| moneyflow | 每日 | 16:30 | `moneyflow` |
| moneyflow_hsgt | 每日 | 17:00 | `moneyflow_hsgt` |
| top_list | 每日 | 18:00 | `top_list` |
| top_inst | 每日 | 18:00 | `top_inst` |
| limit_list | 每日 | 16:30 | `limit_list_d` |
| index_daily | 每日 | 16:00 | `index_daily` |
| index_sw_daily | 每日 | 16:30 | `sw_daily` |
| hk_daily | - | - | ⚠️ 需单独购买权限(1000元/年) |
| margin | 每日 | 18:30 | `margin` |
| stock_basic | 每周 | 周六 | `stock_basic` |
| income | 每季度 | 财报后 | `income_vip` |

### 5.2 ETL 脚本位置

```
DataFetch/
├── FetchDataClass.py    # 基础数据获取类
├── sync_daily.py        # 每日行情同步
├── sync_moneyflow.py    # 资金流向同步
├── sync_toplist.py      # 龙虎榜同步
├── sync_limit.py        # 涨跌停同步
├── sync_index.py        # 指数数据同步
├── sync_hk.py           # 港股数据同步
└── sync_margin.py       # 融资融券同步
```

---

## 6. 前端页面布局（更新）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header: Stock BI    📅 2025-01-31 (周五) 最后更新 16:30    [刷新] [设置]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │     市场快照卡片 (6个)                                              │   │
│  │  [上证↑0.5%] [深证↑0.8%] [涨跌2847/1985] [涨停87] [北向+78亿] [融资+23亿] │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────┬────────────────────────────┐   │
│  │                                        │                            │   │
│  │          主图表区域 (70%)              │      Chat 对话区域 (30%)   │   │
│  │                                        │                            │   │
│  │   Tab: [板块] [资金] [龙虎榜] [涨停]   │  ┌────────────────────┐   │   │
│  │                                        │  │  对话历史           │   │   │
│  │   ┌──────────────────────────────┐    │  │  User: ...         │   │   │
│  │   │                              │    │  │  AI: ...           │   │   │
│  │   │     当前选中的图表            │    │  │                    │   │   │
│  │   │                              │    │  └────────────────────┘   │   │
│  │   │                              │    │                            │   │
│  │   └──────────────────────────────┘    │  ┌────────────────────┐   │   │
│  │                                        │  │  [快捷命令按钮]    │   │   │
│  │   ┌────────────────┬────────────┐    │  │  [资金流向] [龙虎榜]│   │   │
│  │   │   辅助图表1    │   辅助图表2 │    │  │  [涨停分析] [行业]  │   │   │
│  │   │   (成交趋势)   │   (北向资金)│    │  └────────────────────┘   │   │
│  │   └────────────────┴────────────┘    │                            │   │
│  │                                        │  ┌────────────────────┐   │   │
│  └────────────────────────────────────────┤  │  [输入框] [发送]   │   │   │
│                                           │  └────────────────────┘   │   │
└───────────────────────────────────────────┴────────────────────────────┘
```

---

## 7. 开发阶段规划（更新）

### Phase 1: 基础行情（已完成）
- [x] daily_kline 表和 API
- [x] 市场概览卡片
- [x] 涨跌分布图
- [x] 涨幅排行榜
- [x] Chat 基础交互

### Phase 2: 资金流向（新增）
- [ ] 同步 `moneyflow_hsgt` 北向资金
- [ ] 同步 `moneyflow` 个股资金流向
- [ ] 北向资金趋势图
- [ ] 主力净流入排行
- [ ] Chat 支持资金查询

### Phase 3: 龙虎榜 + 涨跌停（新增）
- [ ] 同步 `top_list`, `top_inst` 龙虎榜
- [ ] 同步 `limit_list_d` 涨跌停
- [ ] 龙虎榜明细展示
- [ ] 涨停梯队统计
- [ ] 连板股分析

### Phase 4: 行业 + 指数（新增）
- [ ] 同步 `index_daily` 大盘指数
- [ ] 同步 `index_sw_daily` 申万行业指数
- [ ] 同步 `stock_basic` + `industry_sw`
- [ ] 行业热力图
- [ ] 行业轮动分析

### Phase 5: 港股 + 融资融券（新增）
- [ ] 同步 `hk_basic` 港股基础信息 (2000积分)
- [ ] 同步 `ggt_daily` 港股通成交统计 (2000积分)
- [x] ~~`hk_daily`~~ (需单独购买权限1000元/年，非积分制)
- [ ] 同步 `margin` 融资融券
- [ ] 港股通分析
- [ ] 两融分析

### Phase 6: 财务 + 估值（新增）
- [ ] 同步 `daily_basic` 每日指标
- [ ] 同步 `income` 利润表
- [ ] 估值分布分析
- [ ] 财务指标筛选

---

## 8. TuShare 接口速查

| 功能 | 接口 | 积分要求 | 说明 |
|------|------|----------|------|
| 日K线 | `pro.daily()` | 120+ | A股日线行情 |
| 复权因子 | `pro.adj_factor()` | 120+ | 前/后复权 |
| 每日指标 | `pro.daily_basic()` | 120+ | PE/PB/换手率等 |
| 股票列表 | `pro.stock_basic()` | 120+ | 基础信息 |
| 资金流向 | `pro.moneyflow()` | 2000+ | 个股资金 |
| 北向资金 | `pro.moneyflow_hsgt()` | 120+ | 沪深港通 |
| 龙虎榜 | `pro.top_list()` | 300+ | 每日榜单 |
| 龙虎榜机构 | `pro.top_inst()` | 300+ | 机构明细 |
| 涨跌停 | `pro.limit_list_d()` | 2000+ | 涨跌停榜 |
| 指数日线 | `pro.index_daily()` | 120+ | 大盘指数 |
| 申万日线 | `pro.sw_daily()` | 2000+ | 行业指数 |
| 港股日线 | `pro.hk_daily()` | **单独权限** | ⚠️需购买(1000元/年) |
| 融资融券 | `pro.margin()` | 120+ | 两融汇总 |
| 利润表 | `pro.income_vip()` | 5000+ | 全市场财报 |

**参考文档**: https://tushare.pro/document/2

---

## 9. 附录：示例 SQL 查询（扩展）

### 9.1 北向资金近30日
```sql
SELECT trade_date, north_money,
       SUM(north_money) OVER (ORDER BY trade_date ROWS 4 PRECEDING) as sum_5d
FROM moneyflow_hsgt
ORDER BY trade_date DESC
LIMIT 30;
```

### 9.2 今日主力净流入 Top 20
```sql
SELECT m.ts_code, b.name, m.net_mf_amount, k.pct_chg
FROM moneyflow m
JOIN stock_basic b ON m.ts_code = b.ts_code
JOIN daily_kline k ON m.ts_code = k.ts_code AND m.trade_date = k.trade_date
WHERE m.trade_date = '20250131'
ORDER BY m.net_mf_amount DESC
LIMIT 20;
```

### 9.3 连板股统计
```sql
SELECT ts_code, name, 
       COUNT(*) as board_days,
       MIN(trade_date) as start_date
FROM limit_list
WHERE `limit` = 'U'
  AND trade_date >= DATE_SUB(CURDATE(), INTERVAL 10 DAY)
GROUP BY ts_code, name
HAVING board_days >= 2
ORDER BY board_days DESC;
```

### 9.4 行业资金流向
```sql
SELECT i.industry_l1, 
       SUM(m.net_mf_amount) as total_net_flow,
       COUNT(*) as stock_count
FROM moneyflow m
JOIN industry_sw i ON m.ts_code = i.ts_code
WHERE m.trade_date = '20250131'
GROUP BY i.industry_l1
ORDER BY total_net_flow DESC;
```

---

## 10. 实时数据更新功能（v2.1 新增）

### 10.1 WebSocket 实时推送

当数据库数据更新时，前端自动刷新展示：

```
┌─────────────────────────────────────────────────────────────┐
│  数据流: 数据库 → 后端检测 → WebSocket → 前端自动刷新       │
└─────────────────────────────────────────────────────────────┘

后端:
- /ws/market - WebSocket 连接端点
- 每30秒检测 daily_kline 最新日期变化
- 数据变化时推送 {"type": "data_updated", "trade_date": "20260207"}
- 支持手动触发: POST /api/market/notify-update

前端:
- 自动重连机制
- 收到更新通知后刷新数据
- 显示更新状态提示
```

### 10.2 增强数据可视化（v2.1）

#### 10.2.1 行业热力图 Treemap（点击查看个股）

```
┌─────────────────────────────────────────────────────────────────────────┐
│  行业热力图 Top20（...）              [Top: 10 | 20 | 30 | 50 ▼]        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┬─────────────┬──────────┬─────────┬────────┐          │
│  │   半导体      │   计算机    │  医药     │  电子    │  汽车   │          │
│  │   +5.23%     │   +3.87%    │  +2.95%   │  +2.15% │ +1.68% │          │
│  │   (大方块)    │   (中方块)   │  (绿色)   │         │        │          │
│  ├──────────────┼─────────────┼──────────┼─────────┼────────┤          │
│  │   银行       │   保险      │  房地产   │  ...     │ ...    │          │
│  │   -0.52%     │   -1.23%    │  -2.15%   │          │        │          │
│  └──────────────┴─────────────┴──────────┴─────────┴────────┘          │
└─────────────────────────────────────────────────────────────────────────┘

方块大小: 近5个交易日平均涨幅的绝对值（强度越大方块越大）
方块颜色: 当日涨跌幅
  - 涨幅 ≥3%: 深红 #c0392b
  - 涨幅 1-3%: 红色 #ef5350
  - 涨幅 0-1%: 浅红 #ff7675
  - 平盘: 灰色 #636e72
  - 跌幅 0-1%: 浅绿 #81ecec
  - 跌幅 1-3%: 绿色 #26a69a
  - 跌幅 ≥3%: 深绿 #00695c

Tooltip 悬停显示:
- 行业名称
- 今日涨跌幅
- 近5日平均涨幅
- 上涨/下跌家数
- 点击查看个股提示

点击交互:
- 点击任意方块 → 打开行业股票列表弹窗
```

#### 10.2.2 行业详情弹窗（K线图 + 股票列表）

点击行业热力图方块后，进入行业详情弹窗，包含两个视图：

**视图一：行业K线图（默认）**
```
┌───────────────────────────────────────────────────────────────────────────┐
│  半导体 行业    共 107 只 | ↑95 | ↓12     [K线图 | 股票列表]         [✕]  │
├───────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    半导体（申万）指数走势                           │  │
│  │     ▁▃▅▇█▆▄▅▆▇█▅▃▁▂▄▆█▇▅▃▂▁▃▅▇█▆▄▅▆▇█▅▃▁                          │  │
│  │     (60日 ECharts K线图 + 成交量)                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐                      │
│  │今日涨跌  │收盘点位  │成交额    │PE       │上涨/下跌│                      │
│  │ +2.35%  │ 3256.78 │ 125.6亿 │ 45.2    │ 95/12  │                      │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘                      │
│                    [查看成分股列表 →]                                      │
└───────────────────────────────────────────────────────────────────────────┘

数据来源: index_sw_daily (申万行业指数日线)
```

**视图二：成分股列表**
```
┌───────────────────────────────────────────────────────────────────────────┐
│  半导体 行业    共 107 只 | ↑95 | ↓12     [K线图 | 股票列表]         [✕]  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                    [涨幅↓ | 涨幅↑]        │
│  #   代码      名称      涨跌幅    收盘     成交额    换手率   PE    市值  │
├───────────────────────────────────────────────────────────────────────────┤
│  1   688981    中芯国际  +10.02%   85.50    12.5亿    8.56%   35.2  2850亿 │
│  2   002371    北方华创  +9.87%    320.00   8.3亿     5.32%   120.5 3200亿 │
│  3   603501    韦尔股份  +8.56%    118.20   5.6亿     4.21%   45.8  1380亿 │
│  ...                                                                       │
│  (点击行 → 打开股票详情弹窗，查看K线图)                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

功能:
- **K线图视图**（默认）
  - 显示申万行业指数60日K线图
  - 今日数据卡片：涨跌幅、收盘点位、成交额、PE、上涨/下跌家数
  - 点击"查看成分股列表"切换到股票列表
- **股票列表视图**
  - 展示该行业所有股票（最多200只）
  - 支持涨跌幅排序切换（降序/升序，默认降序）
  - 显示股票基本信息：代码、名称、涨跌幅、收盘价、成交额、换手率、PE、市值
  - 点击任意行 → 打开股票详情弹窗，查看个股K线图

#### 10.2.3 排行热力图 Treemap（点击查看K线）

```
┌─────────────────────────────────────────────────────────────────────────┐
│  涨幅排行 Top20（...）   [Top: 10|20|30|50 ▼]  [涨幅榜 | 跌幅榜]        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┬─────────────┬──────────┬─────────┬────────┐          │
│  │   平安银行    │   招商银行   │  中信证券 │  贵州茅台│ 比亚迪  │          │
│  │   +10.02%    │   +9.87%    │  +8.56%   │  +5.23% │ +4.15% │          │
│  │   (深红大块)  │   (红色)     │  (红色)   │         │        │          │
│  ├──────────────┼─────────────┼──────────┼─────────┼────────┤          │
│  │   ...更多股票...                                          │          │
│  └──────────────┴─────────────┴──────────┴─────────┴────────┘          │
└─────────────────────────────────────────────────────────────────────────┘

方块大小: 成交额（成交额越大方块越大）
方块颜色: 涨跌幅
  - 涨停 ≥9.9%: 深红 #8b0000
  - 涨幅 ≥5%: 暗红 #c0392b
  - 涨幅 3-5%: 红色 #e74c3c
  - 涨幅 1-3%: 浅红 #ef5350
  - 涨幅 0-1%: 粉红 #ff7675
  - 平盘: 灰色 #636e72
  - 跌幅 0-1%: 浅绿 #81ecec
  - 跌幅 1-3%: 绿色 #26a69a
  - 跌幅 3-5%: 深绿 #00b894
  - 跌停 ≤-9.9%: 墨绿 #004d40

Tooltip 悬停显示:
- 股票名称、代码
- 涨跌幅
- 收盘价
- 成交额
- 点击查看K线提示

点击交互:
- 点击任意方块 → 打开股票详情弹窗，显示K线图
- 支持涨幅榜/跌幅榜切换
```

#### 10.2.4 股票详情弹窗

弹窗通过 API `/api/market/stock/{ts_code}` 获取数据，包含 60 日 K 线图（ECharts 蜡烛图+成交量）。

```
┌────────────────────────────────────────────────────────────────────┐
│  [×] 平安银行 (000001.SZ)  +10.02%                                 │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌──────────────────────────────┐ │
│  │   K线图 (60日)              │  │  公司信息                    │ │
│  │   ▁▃▅▇█▆▄▅▆▇█▅▃▁          │  │  行业: 银行                  │ │
│  │   (ECharts 蜡烛图)          │  │  地区: 广东                  │ │
│  │   + 成交量柱状图            │  │  市场: 主板                  │ │
│  └─────────────────────────────┘  │  上市日期: 1991-04-03        │ │
│                                   └──────────────────────────────┘ │
│  ┌─────────────────────────────┐  ┌──────────────────────────────┐ │
│  │  今日数据                    │  │  估值指标                    │ │
│  │  开: 11.23    高: 12.45     │  │  PE: 6.80     PE(TTM): 7.20  │ │
│  │  低: 11.18    收: 12.35     │  │  PB: 0.65                    │ │
│  │  成交量: 285万手            │  │  总市值: 2398亿              │ │
│  │  成交额: 32.5亿             │  │  流通市值: 1856亿            │ │
│  │  换手率: 2.35%   量比: 1.25 │  │                              │ │
│  └─────────────────────────────┘  └──────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘

触发方式:
- 排行榜图表: 点击柱状图或 Y 轴股票名称
- 聊天消息: 点击股票名称链接（蓝色带箭头提示）
- 快捷键: ESC 关闭弹窗
```

### 10.3 数据一致性保障（v2.2 新增）

确保所有看板数据来自同一交易日，避免可视化误导。

#### 10.3.1 一致性检查机制

```
┌─────────────────────────────────────────────────────────────────┐
│  检查的核心数据表:                                                │
│  - daily_kline    (日K线)        ← 主日期基准                    │
│  - daily_basic    (每日指标)                                     │
│  - moneyflow_hsgt (北向资金)                                     │
│  - index_daily    (指数数据)                                     │
└─────────────────────────────────────────────────────────────────┘

API 响应中的 data_consistency 字段:
{
    "consistent": true/false,
    "primary_date": "20260124",
    "warnings": ["每日指标(daily_basic)最新日期为20260123，与主日期不一致"]
}
```

#### 10.3.2 前端警告提示

```
数据一致时: 无提示，正常展示
数据不一致时: 
┌────────────────────────────────────────────────────────────────┐
│ ⚠️ 数据日期不一致: 每日指标最新日期为20260123，与主日期不一致 [×] │
└────────────────────────────────────────────────────────────────┘
橙色警告横幅显示在页面顶部，点击 × 可关闭
```

### 10.4 性能优化策略

#### 10.4.1 前端优化
- **数据分页**: 排行榜默认显示 Top 20，支持 Top 5/10/15/20 切换
- **图表懒加载**: 弹窗内 K 线图延迟 50ms 渲染确保容器尺寸正确
- **防抖节流**: Top N 选择器、涨跌榜切换添加防抖
- **缓存状态**: 排名数据缓存在 state.rankingData 供点击使用

#### 10.4.2 后端优化
- **预计算表**: `market_daily_summary` 存储每日聚合数据
- **缓存机制**: 5分钟 TTL 的内存缓存（SimpleCache）
- **索引优化**: 按查询模式建立复合索引
- **连接池**: SQLAlchemy QueuePool，pool_size=5, max_overflow=10

#### 10.4.3 数据库索引策略
```sql
-- 板块统计优化
CREATE INDEX idx_kline_date_code_prefix ON daily_kline (trade_date, SUBSTRING(ts_code, 1, 2));

-- 行业排名优化
CREATE INDEX idx_sw_date_chg ON index_sw_daily (trade_date, pct_change);

-- 股票详情查询优化
CREATE INDEX idx_company_ts ON stock_company (ts_code);
CREATE INDEX idx_basic_date_ts ON daily_basic (trade_date, ts_code);
```

### 10.5 完整 API 端点清单

#### 核心数据 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/latest-date` | GET | 获取最新交易日期 | - |
| `/api/market/summary` | GET | **核心API** - 完整市场汇总（含一致性检查） | `trade_date` |
| `/api/market/overview` | GET | 市场概览数据 | `trade_date` |
| `/api/market/distribution` | GET | 涨跌幅分布 | `trade_date` |
| `/api/market/sectors` | GET | 板块统计 | `trade_date` |
| `/api/market/indices` | GET | 主要指数数据 | `trade_date` |

#### 排行榜与行业 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/ranking` | GET | 股票排行榜 | `trade_date`, `sort_by`, `order`, `market`, `limit` |
| `/api/market/ranking-enhanced` | GET | 增强排行榜（多维筛选） | `sort_by`, `order`, `top`, `market`, `industry` |
| `/api/market/industries` | GET | 申万行业排名 | `trade_date`, `limit` |
| `/api/market/industries-enhanced` | GET | 增强行业排名（涨跌榜切换） | `top`, `order`, `trade_date` |
| `/api/market/sectors-enhanced` | GET | 增强板块统计（含涨跌家数分布） | `top`, `filter_type`, `trade_date` |
| `/api/market/industry-flow` | GET | 行业资金流向 | `trade_date` |

#### 资金与龙虎榜 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/north-money` | GET | 北向资金（单日） | `trade_date` |
| `/api/market/north-money-trend` | GET | 北向资金趋势 | `days` (7-90) |
| `/api/market/moneyflow/{ts_code}` | GET | 个股资金流向 | `ts_code`, `trade_date` |
| `/api/market/top-list` | GET | 龙虎榜明细 | `trade_date`, `limit` |
| `/api/market/top-list-summary` | GET | 龙虎榜汇总 | `trade_date` |

#### 趋势与统计 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/amount-trend` | GET | 成交额趋势 | `days` (7-90) |
| `/api/market/limit-trend` | GET | 涨停趋势 | `days` (7-90) |
| `/api/market/limit-stats` | GET | 涨跌停统计 | `trade_date` |

#### 行业详情 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/industry-detail/{industry}` | GET | **行业详情**（K线数据+今日统计） | `industry`, `trade_date`, `kline_limit` |
| `/api/market/industry-stocks/{industry}` | GET | **行业所有股票列表**（支持涨跌排序） | `industry`, `trade_date`, `order`(desc/asc), `limit` |

#### 个股详情 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/api/market/stock/{ts_code}` | GET | **股票详情**（K线+今日数据+估值） | `ts_code`, `trade_date` |
| `/api/market/company/{ts_code}` | GET | 公司基础信息 | `ts_code` |
| `/api/market/kline/{ts_code}` | GET | 个股K线数据 | `ts_code`, `limit` |
| `/api/market/search` | GET | 搜索股票 | `keyword`, `limit` |

#### 实时更新与管理 API

| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/ws/market` | WebSocket | 实时数据推送 | - |
| `/api/market/notify-update` | POST | 手动触发更新通知 | - |
| `/api/market/data-consistency` | GET | **数据日期一致性检查** | - |
| `/api/market/precompute/{trade_date}` | POST | 手动触发预计算 | `trade_date` |
| `/api/market/clear-cache` | POST | 清空缓存 | - |

---

## 11. 开发阶段规划（v2.2 更新）

### Phase 7: 实时更新 + 交互增强 ✅ 已完成
- [x] WebSocket 实时数据推送
- [x] 板块涨跌分离显示
- [x] 行业 Top N 筛选
- [x] 排行榜增强（多排序、筛选）
- [x] 股票详情弹窗（K线图+今日数据+估值指标）

### Phase 7.5: 数据一致性 + 交互优化 ✅ 已完成
- [x] 多表数据日期一致性检查
- [x] 前端一致性警告横幅
- [x] 排行榜股票名称可点击（Y轴标签）
- [x] 聊天消息股票名称可点击（带箭头提示）
- [x] K线图渲染优化（延迟确保容器尺寸）
- [x] 行业点击查看个股列表（弹出行业股票表格）
- [x] 行业股票列表支持涨跌排序（涨幅升序/降序切换）
- [x] 行业股票列表点击进入K线详情

### Phase 7.6: Treemap 热力图可视化 ✅ 已完成
- [x] **移除板块视图**（简化界面）
- [x] **行业热力图 Treemap**
  - 方块大小 = 近5日平均涨幅强度
  - 方块颜色 = 当日涨跌幅（红涨绿跌）
  - **支持 Top 10/20/30/50 筛选**
  - 点击方块 → 打开行业详情弹窗
- [x] **行业详情弹窗**（两个视图切换）
  - **K线图视图**：显示申万行业指数60日K线 + 今日数据卡片
  - **股票列表视图**：该行业成分股列表，支持涨跌排序
  - 新增 API `/api/market/industry-detail/{industry}`
- [x] **排行热力图 Treemap**
  - 方块大小 = 成交额
  - 方块颜色 = 涨跌幅（深浅表示幅度）
  - 点击方块 → 打开股票K线详情
  - **支持 Top 10/20/30/50 筛选**
  - 支持涨幅榜/跌幅榜切换
- [x] **后端近5日平均涨幅计算**（precompute.py 增加 avg5_pct_chg 字段）

### Phase 8: 高级可视化（待开发）
- [ ] 资金流向桑基图
- [ ] 涨停梯队可视化
- [ ] 多时间周期对比

---

## 12. 项目文件结构

```
Stock_BI/claude/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主入口，注册路由，启动 WebSocket 监控
│   ├── config.py            # 配置（数据库连接、API 端口等）
│   ├── database.py          # SQLAlchemy 引擎和会话管理
│   ├── cache.py             # SimpleCache 内存缓存
│   ├── models.py            # 数据库模型
│   ├── precompute.py        # 预计算模块（market_daily_summary）
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── market.py        # 市场数据 API（20+ 端点）
│   │   ├── chat.py          # Chat 交互 API
│   │   └── websocket.py     # WebSocket 实时推送
│   └── services/
│       ├── __init__.py
│       └── llm.py           # LLM 服务（可选）
├── frontend/
│   ├── index.html           # 主页面（指数栏、卡片、图表、聊天、弹窗）
│   ├── styles.css           # 深色主题样式（1000+ 行）
│   └── app.js               # 前端逻辑（WebSocket、图表、交互）
├── requirements.txt         # Python 依赖
├── requirements.md          # 本文档
├── run.sh                   # 启动脚本
├── add_indexes.sql          # 数据库索引创建脚本
└── README.md                # 项目说明
```

---

*文档版本：v2.3*  
*更新日期：2026-01-24*  
*数据源：TuShare Pro (5000+ 积分)*

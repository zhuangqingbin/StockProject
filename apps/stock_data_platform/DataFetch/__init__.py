"""
DataFetch - TuShare 数据获取模块

使用示例:
    from DataFetch import StockDailyFetch, MoneyFlowHSGTFetch
    
    # 获取 A 股日线
    fetcher = StockDailyFetch()
    df = fetcher.fetch(trade_date='20250131')
    
    # 获取北向资金
    fetcher = MoneyFlowHSGTFetch()
    df = fetcher.fetch(start_date='20250101', end_date='20250131')
"""

# 基础类
from .BaseClass import BaseDataFetch
from .client import TuShareClient, ClientConfig

# 股票基础信息
from .FetchBasic import (
    StockBasicFetch,        # 股票基础信息
    TradeCalFetch,          # 交易日历
    StockCompanyFetch,      # 上市公司信息
)

# A股日线行情
from .FetchDaily import (
    StockDailyFetch,        # A股日线行情
    StockDailyBasicFetch,   # 每日指标(PE/PB/换手率等)
)

# 资金流向数据
from .FetchMoneyFlow import (
    MoneyFlowFetch,         # 个股资金流向
    MoneyFlowHSGTFetch,     # 沪深港通资金流向
    HSGTTop10Fetch,         # 沪深港通十大成交股
)

# 龙虎榜数据
from .FetchTopList import (
    TopListFetch,           # 龙虎榜每日明细
    TopInstFetch,           # 龙虎榜机构交易明细
)

# 涨跌停数据
from .FetchLimit import (
    LimitListFetch,         # 每日涨跌停统计
    StkLimitFetch,          # 每日涨跌停价格
)

# 指数数据
from .FetchIndex import (
    IndexDailyFetch,        # 指数日线行情
    IndexBasicFetch,        # 指数基本信息
    SWIndexDailyFetch,      # 申万行业指数日线
    IndexClassifyFetch,     # 申万行业分类
    IndexMemberFetch,       # 申万行业成分股
    MAIN_INDEX_CODES,       # 常用指数代码
)

# 港股数据 (注意: hk_daily需要单独购买权限1000元/年, 不是积分制度)
from .FetchHK import (
    HKBasicFetch,           # 港股基础信息 (2000积分)
    GGTDailyFetch,          # 港股通每日成交统计 (2000积分)
)

# 融资融券数据
from .FetchMargin import (
    MarginFetch,            # 融资融券每日汇总
    MarginDetailFetch,      # 融资融券交易明细
    MarginTargetFetch,      # 融资融券标的
)

# 财务数据
from .FetchFinancial import (
    IncomeFetch,            # 利润表
    IncomeVipFetch,         # 利润表(VIP,支持全市场)
    BalanceSheetFetch,      # 资产负债表
    BalanceSheetVipFetch,   # 资产负债表(VIP,支持全市场)
    CashFlowFetch,          # 现金流量表
    CashFlowVipFetch,       # 现金流量表(VIP,支持全市场)
    FinaIndicatorFetch,     # 财务指标
    FinaIndicatorVipFetch,  # 财务指标(VIP,支持全市场)
)

# 高级数据 (5000+积分)
from .FetchAdvanced import (
    HKHoldFetch,            # 沪深股通持股明细
    CyqPerfFetch,           # 每日筹码及胜率
    StkFactorFetch,         # 股票技术面因子
    StkAuctionFetch,        # 开盘集合竞价
    BlockTradeFetch,        # 大宗交易
    StkHolderNumberFetch,   # 股东人数
    Top10HoldersFetch,      # 前十大股东
    Top10FloatHoldersFetch, # 前十大流通股东
    DividendFetch,          # 分红送股
    ShareFloatFetch,        # 限售股解禁
    PledgeStatFetch,        # 股权质押统计
)

__all__ = [
    # 基础
    'BaseDataFetch', 'TuShareClient', 'ClientConfig',
    # 股票
    'StockBasicFetch', 'TradeCalFetch', 'StockCompanyFetch',
    'StockDailyFetch', 'StockDailyBasicFetch',
    # 资金
    'MoneyFlowFetch', 'MoneyFlowHSGTFetch', 'HSGTTop10Fetch',
    # 龙虎榜
    'TopListFetch', 'TopInstFetch',
    # 涨跌停
    'LimitListFetch', 'StkLimitFetch',
    # 指数
    'IndexDailyFetch', 'IndexBasicFetch', 'SWIndexDailyFetch',
    'IndexClassifyFetch', 'IndexMemberFetch', 'MAIN_INDEX_CODES',
    # 港股 (注意: hk_daily需要单独购买权限)
    'HKBasicFetch', 'GGTDailyFetch',
    # 融资融券
    'MarginFetch', 'MarginDetailFetch', 'MarginTargetFetch',
    # 财务
    'IncomeFetch', 'IncomeVipFetch',
    'BalanceSheetFetch', 'BalanceSheetVipFetch',
    'CashFlowFetch', 'CashFlowVipFetch',
    'FinaIndicatorFetch', 'FinaIndicatorVipFetch',
    # 高级数据
    'HKHoldFetch', 'CyqPerfFetch', 'StkFactorFetch', 'StkAuctionFetch',
    'BlockTradeFetch', 'StkHolderNumberFetch', 'Top10HoldersFetch',
    'Top10FloatHoldersFetch', 'DividendFetch', 'ShareFloatFetch', 'PledgeStatFetch',
]

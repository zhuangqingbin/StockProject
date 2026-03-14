"""
基础数据获取
TuShare API 文档: https://tushare.pro/document/2?doc_id=25
"""

from .BaseClass import BaseDataFetch


class StockBasicFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=25
    公司基础信息, 2000积分
        获取基础信息数据，包括股票代码、名称、上市日期、退市日期等
    API params:
        ts_code: 股票代码
        name: 股票名称
        market: 市场类别 （主板/创业板/科创板/CDR/北交所）
        list_status: 上市状态 L上市 D退市 P暂停上市 G过会未交易, 默认是L
        exchange: 交易所 SSE上交所 SZSE深交所 BSE北交所
        is_hs: 是否沪深港通标的, N否 H沪股通 S深股通
    """
    def read_data(self, **kwargs):
        self.fields = [
            "ts_code", "symbol", "name", "area", "industry", "market", "exchange", "is_hs", "list_date"
        ]
        return self.client.call(
            "stock_basic",
            exchange="",
            list_status="L",
            fields=','.join(self.fields),
            **kwargs,
        )

class TradeCalFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=26
    交易日历, 2000积分
        获取各大交易所交易日历数据,默认提取的是上交所
    API params:
        exchange: 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        is_open: 是否交易 '0'休市 '1'交易
    
    """
    def read_data(self, start_date, end_date, **kwargs):
        self.fields = [
            "exchange", "cal_date", "is_open"
        ]
        return self.client.call(
            "trade_cal",
            exchange="",
            start_date=start_date,
            end_date=end_date,
            fields=','.join(self.fields),
            **kwargs,
        )



class StockCompanyFetch(BaseDataFetch):
    """
    API: https://tushare.pro/document/2?doc_id=112
    上市公司基本信息, 120积分
        获取上市公司基础信息, 单次提取4500条, 可以根据交易所分批提取
    API params:
        ts_code: 股票代码
        exchange: 交易所代码, SSE上交所 SZSE深交所 BSE北交所
    
    """
    def read_data(self, **kwargs):
        self.fields  = [
            "ts_code", "com_name", "reg_capital", "province", "city", 
            "employees", "main_business", "business_scope"
        ]
        return self.client.call(
            "stock_company",
            exchange="",
            fields=','.join(self.fields),
            **kwargs,
        )


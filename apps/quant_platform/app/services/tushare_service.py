import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
from loguru import logger
from sqlalchemy import select
from app.core.config import TUSHARE_TOKEN
from app.core.database import StockBasic, StockDaily, async_session
import asyncio
import time

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()


class TushareService:
    _last_call_time = 0
    _min_interval = 0.3

    @classmethod
    def _rate_limit(cls):
        elapsed = time.time() - cls._last_call_time
        if elapsed < cls._min_interval:
            time.sleep(cls._min_interval - elapsed)
        cls._last_call_time = time.time()

    @classmethod
    def fetch_stock_list(cls) -> pd.DataFrame:
        cls._rate_limit()
        df = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date,list_status',
        )
        logger.info(f"Fetched {len(df)} stocks")
        return df

    @classmethod
    def fetch_daily(cls, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        cls._rate_limit()
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    @classmethod
    def fetch_daily_basic(cls, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        cls._rate_limit()
        df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    @classmethod
    def fetch_index_daily(cls, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        cls._rate_limit()
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    @classmethod
    def fetch_trade_cal(cls, start_date: str, end_date: str) -> pd.DataFrame:
        cls._rate_limit()
        return pro.trade_cal(start_date=start_date, end_date=end_date)

    @classmethod
    def fetch_top_list(cls, trade_date: str) -> pd.DataFrame:
        cls._rate_limit()
        return pro.top_list(trade_date=trade_date)

    @classmethod
    def fetch_moneyflow(cls, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        cls._rate_limit()
        return pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)


class DataService:
    @staticmethod
    async def get_stock_list(keyword: str = "") -> List[dict]:
        async with async_session() as session:
            if keyword:
                result = await session.execute(
                    select(StockBasic).where(
                        (StockBasic.name.contains(keyword)) |
                        (StockBasic.ts_code.contains(keyword.upper())) |
                        (StockBasic.symbol.contains(keyword))
                    ).limit(50)
                )
            else:
                result = await session.execute(
                    select(StockBasic).limit(100)
                )
            stocks = result.scalars().all()
            return [
                {
                    "ts_code": s.ts_code, "symbol": s.symbol, "name": s.name,
                    "area": s.area, "industry": s.industry, "market": s.market,
                    "list_date": s.list_date,
                }
                for s in stocks
            ]

    @staticmethod
    async def get_daily_data(ts_code: str, start_date: str, end_date: str) -> List[dict]:
        async with async_session() as session:
            result = await session.execute(
                select(StockDaily).where(
                    StockDaily.ts_code == ts_code,
                    StockDaily.trade_date >= start_date,
                    StockDaily.trade_date <= end_date,
                ).order_by(StockDaily.trade_date)
            )
            cached = result.scalars().all()

            if cached:
                return [
                    {
                        "date": r.trade_date, "open": r.open, "high": r.high,
                        "low": r.low, "close": r.close, "volume": r.vol,
                        "amount": r.amount, "pct_chg": r.pct_chg,
                        "pre_close": r.pre_close, "change": r.change,
                    }
                    for r in cached
                ]

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, TushareService.fetch_daily, ts_code, start_date, end_date
            )

            if df is None or df.empty:
                return []

            for _, row in df.iterrows():
                obj = StockDaily(
                    ts_code=row['ts_code'], trade_date=row['trade_date'],
                    open=row['open'], high=row['high'], low=row['low'],
                    close=row['close'], pre_close=row.get('pre_close'),
                    change=row.get('change'), pct_chg=row.get('pct_chg'),
                    vol=row.get('vol'), amount=row.get('amount'),
                )
                session.add(obj)

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.warning(f"Cache write conflict (data may already exist): {e}")

            return [
                {
                    "date": row['trade_date'], "open": row['open'], "high": row['high'],
                    "low": row['low'], "close": row['close'], "volume": row.get('vol', 0),
                    "amount": row.get('amount', 0), "pct_chg": row.get('pct_chg', 0),
                    "pre_close": row.get('pre_close', 0), "change": row.get('change', 0),
                }
                for _, row in df.iterrows()
            ]

    @staticmethod
    def compute_indicators(data: List[dict], indicators: List[str]) -> dict:
        df = pd.DataFrame(data)
        if df.empty:
            return {"data": data, "indicators": {}}

        result = {}
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        vol = df['volume'].values

        for ind in indicators:
            if ind.startswith('MA') and ind[2:].isdigit():
                period = int(ind[2:])
                result[ind] = pd.Series(close).rolling(period).mean().tolist()

            elif ind.startswith('EMA') and ind[3:].isdigit():
                period = int(ind[3:])
                result[ind] = pd.Series(close).ewm(span=period).mean().tolist()

            elif ind == 'MACD':
                ema12 = pd.Series(close).ewm(span=12).mean()
                ema26 = pd.Series(close).ewm(span=26).mean()
                dif = ema12 - ema26
                dea = dif.ewm(span=9).mean()
                macd = (dif - dea) * 2
                result['DIF'] = dif.tolist()
                result['DEA'] = dea.tolist()
                result['MACD'] = macd.tolist()

            elif ind == 'KDJ':
                low_list = pd.Series(low).rolling(9).min()
                high_list = pd.Series(high).rolling(9).max()
                rsv = (pd.Series(close) - low_list) / (high_list - low_list) * 100
                rsv = rsv.fillna(50)
                k = rsv.ewm(com=2).mean()
                d = k.ewm(com=2).mean()
                j = 3 * k - 2 * d
                result['K'] = k.tolist()
                result['D'] = d.tolist()
                result['J'] = j.tolist()

            elif ind == 'RSI':
                delta = pd.Series(close).diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result['RSI6'] = pd.Series(close).diff().pipe(
                    lambda x: x.where(x > 0, 0).rolling(6).mean() /
                    (-x.where(x < 0, 0).rolling(6).mean())
                ).pipe(lambda x: 100 - 100 / (1 + x)).tolist()
                result['RSI14'] = rsi.tolist()

            elif ind == 'BOLL':
                ma20 = pd.Series(close).rolling(20).mean()
                std20 = pd.Series(close).rolling(20).std()
                result['BOLL_MID'] = ma20.tolist()
                result['BOLL_UP'] = (ma20 + 2 * std20).tolist()
                result['BOLL_DN'] = (ma20 - 2 * std20).tolist()

            elif ind == 'VOL_MA':
                result['VOL_MA5'] = pd.Series(vol).rolling(5).mean().tolist()
                result['VOL_MA10'] = pd.Series(vol).rolling(10).mean().tolist()

        for key in result:
            result[key] = [
                None if (v is None or (isinstance(v, float) and np.isnan(v))) else round(v, 4)
                for v in result[key]
            ]

        return {"data": data, "indicators": result}

    @staticmethod
    async def get_market_overview() -> dict:
        today = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

        indices = {
            '000001.SH': 'Shanghai Composite',
            '399001.SZ': 'Shenzhen Component',
            '399006.SZ': 'ChiNext',
            '000688.SH': 'STAR 50',
        }

        overview = []
        loop = asyncio.get_event_loop()

        for code, name in indices.items():
            try:
                df = await loop.run_in_executor(
                    None, TushareService.fetch_index_daily, code, start, today
                )
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    overview.append({
                        "code": code,
                        "name": name,
                        "close": float(latest['close']),
                        "change": float(latest['close'] - prev['close']),
                        "pct_chg": float(latest.get('pct_chg', 0)),
                        "volume": float(latest.get('vol', 0)),
                        "amount": float(latest.get('amount', 0)),
                        "history": df[['trade_date', 'close']].to_dict('records')[-20:],
                    })
            except Exception as e:
                logger.error(f"Fetch index {code} failed: {e}")

        return {"indices": overview, "updated_at": today}

#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from datetime import datetime, timedelta
from app.core.database import init_db, async_session, StockBasic, StockDaily
from app.services.tushare_service import TushareService
from sqlalchemy import select, func
from loguru import logger
import time


async def batch_download(days: int = 365, batch_size: int = 50, skip_existing: bool = True):
    await init_db()

    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

    async with async_session() as session:
        result = await session.execute(
            select(StockBasic).where(StockBasic.list_status == 'L')
        )
        stocks = result.scalars().all()

    total = len(stocks)
    logger.info(f"Total {total} stocks, range: {start_date} ~ {end_date}")

    success = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch = stocks[i:i + batch_size]

        for stock in batch:
            try:
                if skip_existing:
                    async with async_session() as session:
                        count = (await session.execute(
                            select(func.count(StockDaily.id)).where(
                                StockDaily.ts_code == stock.ts_code,
                                StockDaily.trade_date >= start_date,
                            )
                        )).scalar()
                        if count and count > 100:
                            skipped += 1
                            continue

                df = TushareService.fetch_daily(stock.ts_code, start_date, end_date)
                if df is not None and not df.empty:
                    async with async_session() as session:
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
                            success += 1
                        except Exception:
                            await session.rollback()
                            success += 1
                else:
                    skipped += 1

            except Exception as e:
                failed += 1
                logger.warning(f"Download {stock.ts_code} {stock.name} failed: {e}")

        elapsed = time.time() - start_time
        done = i + len(batch)
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0

        logger.info(
            f"Progress: {done}/{total} ({done / total * 100:.1f}%) | "
            f"OK: {success} Skip: {skipped} Fail: {failed} | "
            f"Rate: {rate:.1f}/s | ETA: {eta / 60:.1f}min"
        )

    elapsed = time.time() - start_time
    logger.info(f"\nDownload complete! Time: {elapsed / 60:.1f}min")
    logger.info(f"OK: {success} | Skip: {skipped} | Fail: {failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch download stock data')
    parser.add_argument('--days', type=int, default=365, help='Download last N days (default 365)')
    parser.add_argument('--batch', type=int, default=50, help='Batch size (default 50)')
    parser.add_argument('--force', action='store_true', help='Force re-download existing data')
    args = parser.parse_args()

    asyncio.run(batch_download(
        days=args.days,
        batch_size=args.batch,
        skip_existing=not args.force,
    ))

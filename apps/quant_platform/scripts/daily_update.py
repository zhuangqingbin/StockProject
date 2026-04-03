#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from datetime import datetime, timedelta
from app.core.database import init_db, async_session, StockBasic, StockDaily
from app.services.tushare_service import TushareService
from sqlalchemy import select, func
from loguru import logger

RETRY_INTERVAL = 600
MAX_RETRIES = 6
BATCH_SIZE = 50


async def update_single_stock(stock, today: str) -> tuple:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(func.max(StockDaily.trade_date)).where(
                    StockDaily.ts_code == stock.ts_code
                )
            )
            last_date = result.scalar()

        start = last_date or (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        if last_date and last_date >= today:
            return (stock.ts_code, True, "up to date")

        df = TushareService.fetch_daily(stock.ts_code, start, today)

        if df is None or df.empty:
            return (stock.ts_code, True, "no new data")

        async with async_session() as session:
            count = 0
            for _, row in df.iterrows():
                if last_date and row['trade_date'] <= last_date:
                    continue
                obj = StockDaily(
                    ts_code=row['ts_code'], trade_date=row['trade_date'],
                    open=row['open'], high=row['high'], low=row['low'],
                    close=row['close'], pre_close=row.get('pre_close'),
                    change=row.get('change'), pct_chg=row.get('pct_chg'),
                    vol=row.get('vol'), amount=row.get('amount'),
                )
                session.add(obj)
                count += 1
            try:
                await session.commit()
                return (stock.ts_code, True, f"+{count} rows")
            except Exception as e:
                await session.rollback()
                return (stock.ts_code, True, f"partial duplicate, +{count} rows")

    except Exception as e:
        return (stock.ts_code, False, str(e))


async def run_update():
    await init_db()

    today = datetime.now().strftime('%Y%m%d')
    start_time = time.time()

    logger.info(f"{'=' * 60}")
    logger.info(f"Daily update started | Date: {today}")
    logger.info(f"{'=' * 60}")

    async with async_session() as session:
        result = await session.execute(
            select(StockBasic).where(StockBasic.list_status == 'L')
        )
        all_stocks = result.scalars().all()

    total = len(all_stocks)
    logger.info(f"Total {total} active stocks to update")

    pending = list(all_stocks)
    retry_count = 0
    total_success = 0

    while pending and retry_count <= MAX_RETRIES:
        if retry_count > 0:
            logger.info(f"Retry #{retry_count} | Waiting {RETRY_INTERVAL // 60}min...")
            logger.info(f"   {len(pending)} stocks remaining")
            await asyncio.sleep(RETRY_INTERVAL)

        round_label = "Initial run" if retry_count == 0 else f"Retry #{retry_count}"
        logger.info(f"--- {round_label} | Processing {len(pending)} stocks ---")

        failed_stocks = []
        success_count = 0

        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i:i + BATCH_SIZE]

            for stock in batch:
                ts_code, success, msg = await update_single_stock(stock, today)

                if success:
                    success_count += 1
                    total_success += 1
                else:
                    failed_stocks.append(stock)
                    logger.warning(f"  FAIL {ts_code} {stock.name}: {msg}")

            done = min(i + BATCH_SIZE, len(pending))
            pct = done / len(pending) * 100
            logger.info(f"  Progress: {done}/{len(pending)} ({pct:.0f}%) | OK: {success_count} Fail: {len(failed_stocks)}")

        logger.info(f"  {round_label} done | OK: {success_count} | Fail: {len(failed_stocks)}")

        if not failed_stocks:
            logger.info("  All stocks updated successfully!")
            break

        pending = failed_stocks
        retry_count += 1

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    logger.info(f"{'=' * 60}")
    logger.info(f"Update summary")
    logger.info(f"  Total stocks:  {total}")
    logger.info(f"  Success:       {total_success}")
    logger.info(f"  Final failed:  {len(pending)}")
    logger.info(f"  Retries:       {retry_count}")
    logger.info(f"  Time:          {minutes}m{seconds}s")

    if pending:
        logger.warning(f"The following {len(pending)} stocks failed after {MAX_RETRIES} retries:")
        for stock in pending[:50]:
            logger.warning(f"  - {stock.ts_code} {stock.name}")
        if len(pending) > 50:
            logger.warning(f"  ... and {len(pending) - 50} more")

    logger.info(f"{'=' * 60}")
    return len(pending) == 0


if __name__ == "__main__":
    success = asyncio.run(run_update())
    sys.exit(0 if success else 1)

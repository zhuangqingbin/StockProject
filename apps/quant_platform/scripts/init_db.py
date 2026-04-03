#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.core.config import QV_MYSQL_DATABASE
from app.core.database import init_db, async_session, StockBasic
from app.services.tushare_service import TushareService
from loguru import logger


async def main():
    logger.info(f"=== Initializing database: {QV_MYSQL_DATABASE} ===")
    await init_db()

    logger.info("=== Downloading stock list ===")
    df = TushareService.fetch_stock_list()

    async with async_session() as session:
        for _, row in df.iterrows():
            obj = StockBasic(
                ts_code=row['ts_code'],
                symbol=row['symbol'],
                name=row['name'],
                area=row.get('area', ''),
                industry=row.get('industry', ''),
                market=row.get('market', ''),
                list_date=row.get('list_date', ''),
                list_status=row.get('list_status', 'L'),
            )
            session.add(obj)

        try:
            await session.commit()
            logger.info(f"Inserted {len(df)} stocks")
        except Exception as e:
            await session.rollback()
            logger.error(f"Insert failed: {e}")

    logger.info("=== Initialization complete ===")


if __name__ == "__main__":
    asyncio.run(main())

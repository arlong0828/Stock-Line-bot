from pathlib import Path
import sys
from datetime import datetime
from dataclasses import dataclass

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import Base
from app.models.stockData import StockHistory
from app.services.stockCrawler import StockCrawlerService


@dataclass
class FakeRow:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    capacity: int


@pytest.mark.anyio
async def test_upsert_history_rows_updates_existing_row_instead_of_inserting_duplicate():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    service = StockCrawlerService()

    first = FakeRow(datetime(2026, 5, 4), 100.0, 110.0, 95.0, 108.0, 1000)
    second = FakeRow(datetime(2026, 5, 4), 101.0, 111.0, 96.0, 109.0, 2000)

    async with Session() as db:
        await service.upsertHistoryRows(db, stockId=1, rows=[first])
        await service.upsertHistoryRows(db, stockId=1, rows=[second])

        records = (await db.execute(select(StockHistory))).scalars().all()
        assert len(records) == 1
        assert records[0].close_price == 109.0
        assert records[0].volume == 2000

    await engine.dispose()

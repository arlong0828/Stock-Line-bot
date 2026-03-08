import asyncio
from sqlalchemy.future import select
from sqlalchemy import func
from app.database.session import AsyncSessionLocal
from app.models.stockData import StockInfo, StockHistory

async def checkCloudProgress():
    async with AsyncSessionLocal() as db:
        print("--- ☁️ 雲端資料庫進度查詢 ---")
        
        # 1. 查詢股票總數
        infoCount = await db.execute(select(func.count(StockInfo.id)))
        # 2. 查詢歷史資料總數
        historyCount = await db.execute(select(func.count(StockHistory.id)))
        
        print(f"已建立的股票數量: {infoCount.scalar()} 支")
        print(f"目前的歷史股價總數: {historyCount.scalar()} 筆")
        print("----------------------------")

if __name__ == "__main__":
    asyncio.run(checkCloudProgress())

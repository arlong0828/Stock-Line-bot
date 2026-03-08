import twstock
import asyncio
from collections import namedtuple
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.stockData import StockInfo, StockHistory
from app.database.session import AsyncSessionLocal
import logging

# --- Monkey Patch ---
if len(twstock.stock.DATATUPLE._fields) < 11:
    new_fields = twstock.stock.DATATUPLE._fields + ('unknown',)
    twstock.stock.DATATUPLE = namedtuple('Data', new_fields)
# --------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockCrawlerService:
    def isEtf(self, symbol: str) -> bool:
        if symbol.startswith("00") and len(symbol) >= 4:
            return True
        codeInfo = twstock.codes.get(symbol)
        if codeInfo and "ETF" in codeInfo.type:
            return True
        return False

    async def getOrCreateStockInfo(self, db: AsyncSession, symbol: str) -> StockInfo:
        result = await db.execute(select(StockInfo).filter(StockInfo.symbol == symbol))
        stockInfo = result.scalars().first()

        if not stockInfo:
            codeInfo = twstock.codes.get(symbol)
            name = codeInfo.name if codeInfo else "未知股票"
            isEtf = self.isEtf(symbol)

            stockInfo = StockInfo(symbol=symbol, name=name, is_etf=isEtf)
            db.add(stockInfo)
            await db.commit()
            await db.refresh(stockInfo)
            print(f"DEBUG: [資料庫] 已建立股票資訊: {symbol} ({name}), ETF: {isEtf}")
        
        return stockInfo

    async def fetch10YearHistory(self, symbol: str):
        """爬取 10 年歷史資料"""
        async with AsyncSessionLocal() as db:
            stockInfo = await self.getOrCreateStockInfo(db, symbol)
            stockId, stockName = stockInfo.id, stockInfo.name
            
            endDate = datetime.now()
            startDate = endDate - relativedelta(years=10)
            
            loop = asyncio.get_event_loop()
            stock = twstock.Stock(symbol, initial_fetch=False)
            
            currentDate = startDate
            totalRecords = 0

            while currentDate <= endDate:
                year, month = currentDate.year, currentDate.month
                print(f"DEBUG: [爬蟲] 正在抓取 {symbol} ({stockName}) 資料: {year}/{month}")
                
                try:
                    data = await loop.run_in_executor(None, stock.fetch, year, month)
                    if data:
                        for d in data:
                            historyEntry = StockHistory(
                                stock_id=stockId, date=d.date, open_price=d.open,
                                high_price=d.high, low_price=d.low, close_price=d.close,
                                volume=int(d.capacity)
                            )
                            await db.merge(historyEntry)
                        await db.commit()
                        totalRecords += len(data)
                except Exception as e:
                    await db.rollback()
                    if "UNIQUE constraint failed" not in str(e):
                        print(f"ERROR: [爬蟲] {symbol} {year}/{month} 失敗: {str(e)}")
                
                currentDate += relativedelta(months=1)
                await asyncio.sleep(0.5)

            print(f"DONE: [完成] {symbol} 歷史資料爬取完畢，共 {totalRecords} 筆。")
            return totalRecords

    async def updateAllStocksData(self):
        """每日收盤自動更新：更新所有已存在資料庫中的股票最新資料"""
        async with AsyncSessionLocal() as db:
            # 1. 取得資料庫中所有的股票
            result = await db.execute(select(StockInfo))
            allStocks = result.scalars().all()
            
            if not allStocks:
                print("DEBUG: [自動更新] 資料庫目前沒有任何股票。")
                return

            print(f"DEBUG: [自動更新] 開始更新 {len(allStocks)} 支股票的最新資料...")
            
            now = datetime.now()
            year, month = now.year, now.month
            loop = asyncio.get_event_loop()

            for stockInfo in allStocks:
                symbol = stockInfo.symbol
                print(f"DEBUG: [自動更新] 正在同步 {symbol} ({stockInfo.name})...")
                
                try:
                    stock = twstock.Stock(symbol, initial_fetch=False)
                    data = await loop.run_in_executor(None, stock.fetch, year, month)
                    
                    if data:
                        for d in data:
                            historyEntry = StockHistory(
                                stock_id=stockInfo.id, date=d.date, open_price=d.open,
                                high_price=d.high, low_price=d.low, close_price=d.close,
                                volume=int(d.capacity)
                            )
                            await db.merge(historyEntry)
                        await db.commit()
                        print(f"DEBUG: [自動更新] {symbol} 同步完成。")
                except Exception as e:
                    await db.rollback()
                    print(f"ERROR: [自動更新] {symbol} 失敗: {str(e)}")
                
                await asyncio.sleep(1) # 每日更新稍微慢一點，對伺服器更友善

            print("DONE: [自動更新] 全數股票資料同步完畢。")

stockCrawlerService = StockCrawlerService()

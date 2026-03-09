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
            if not codeInfo:
                return None
                
            name = codeInfo.name
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
        """每日收盤自動更新"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(StockInfo))
            allStocks = result.scalars().all()
            
            if not allStocks:
                return

            print(f"DEBUG: [自動更新] 開始同步 {len(allStocks)} 支股票...")
            
            for stockInfo in allStocks:
                # 為了防止連線池爆炸，我們每一支股票都分開開啟 Session
                asyncio.create_task(self.fetch10YearHistory(stockInfo.symbol))
                await asyncio.sleep(2) # 延遲啟動，避免瞬間耗盡連線

stockCrawlerService = StockCrawlerService()

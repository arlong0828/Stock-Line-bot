import re
import asyncio
from app.services.stockCrawler import stockCrawlerService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import update, select
from app.models.stockData import StockInfo, User
import logging

logger = logging.getLogger(__name__)

class LineBotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stockCrawler = stockCrawlerService

    async def getOrCreateUser(self, lineUserId: str) -> User:
        """取得或建立使用者資料 (預先載入關注清單)"""
        # 使用 selectinload 確保關聯屬性在非同步下可用
        result = await self.db.execute(
            select(User)
            .filter(User.lineUserId == lineUserId)
            .options(selectinload(User.watchedStocks))
        )
        user = result.scalars().first()
        if not user:
            user = User(lineUserId=lineUserId)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            # 新使用者需要重新載入關聯屬性
            result = await self.db.execute(
                select(User).filter(User.id == user.id).options(selectinload(User.watchedStocks))
            )
            user = result.scalars().first()
            print(f"DEBUG: [使用者] 已註冊新使用者: {lineUserId}")
        return user

    async def handleWatchStock(self, lineUserId: str, symbols: list):
        """處理關注股票請求：建立使用者與股票的關聯，並自動觸發歷史爬取"""
        user = await self.getOrCreateUser(lineUserId)

        for symbol in symbols:
            try:
                # 1. 確保股票資訊已建立
                stockInfo = await self.stockCrawler.getOrCreateStockInfo(self.db, symbol)

                # 2. 建立關注關聯
                if stockInfo not in user.watchedStocks:
                    user.watchedStocks.append(stockInfo)
                    stockInfo.isWatched = True
                    await self.db.commit()
                    print(f"DEBUG: [關注] 使用者 {lineUserId} 已關注 {symbol}")

                    # 3. 聯動機制：自動啟動 10 年歷史爬取 (如果之前沒加入過)
                    print(f"DEBUG: [聯動] 偵測到新關注，自動啟動 {symbol} 歷史爬取...")
                    asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))
                else:
                    print(f"DEBUG: [關注] 使用者 {lineUserId} 之前已關注過 {symbol}")
            except Exception as e:
                await self.db.rollback()
                print(f"ERROR: [關注] 處理 {symbol} 失敗: {str(e)}")


    async def handleJoinStock(self, symbols: list):
        """處理加入股票請求：背景爬取 10 年歷史資料 (維持靜音)"""
        for symbol in symbols:
            print(f"DEBUG: [Line] 正在啟動 {symbol} 的 10 年歷史爬取任務...")
            asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))

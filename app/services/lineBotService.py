import re
import asyncio
from app.services.stockCrawler import stockCrawlerService
from app.services.breakoutService import breakoutService
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
        self.breakoutService = breakoutService

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
            logger.info("已註冊新的 LINE 使用者")
        return user

    async def handleWatchStock(self, lineUserId: str, symbols: list):
        """處理關注股票請求：建立使用者與股票的關聯"""
        user = await self.getOrCreateUser(lineUserId)
        
        for symbol in symbols:
            try:
                # 確保股票資訊已建立
                stockInfo = await self.stockCrawler.getOrCreateStockInfo(self.db, symbol)
                
                # 檢查是否已經關注過 (現在 user.watchedStocks 已經預先載入了)
                if stockInfo not in user.watchedStocks:
                    user.watchedStocks.append(stockInfo)
                    # 同時標記系統級關注 (用於 13:35 報告)
                    stockInfo.isWatched = True
                    await self.db.commit()
                    logger.info("LINE 使用者已關注股票 %s", symbol)
                else:
                    logger.info("LINE 使用者先前已關注股票 %s", symbol)
            except Exception as e:
                await self.db.rollback()
                print(f"ERROR: [關注] 處理 {symbol} 失敗: {str(e)}")

    async def handleJoinStock(self, symbols: list):
        """處理加入股票請求：背景爬取 10 年歷史資料 (維持靜音)"""
        for symbol in symbols:
            print(f"DEBUG: [Line] 正在啟動 {symbol} 的 10 年歷史爬取任務...")
            asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))

    async def handleBreakoutAnalysis(self, limit: int = 5) -> str:
        """產生飆股候選分析報告"""
        return await self.breakoutService.getBreakoutReport(limit=limit)

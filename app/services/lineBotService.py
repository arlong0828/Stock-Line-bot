import re
import asyncio
from app.services.stockCrawler import stockCrawlerService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import update, select
from app.models.stockData import StockInfo, User
from app.core.config import settings
from linebot.v3.messaging import (
    AsyncMessagingApi,
    AsyncApiClient,
    Configuration,
    TextMessage,
    ReplyMessageRequest
)
import logging

logger = logging.getLogger(__name__)
lineConfig = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

class LineBotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.stockCrawler = stockCrawlerService

    async def replyText(self, replyToken: str, text: str):
        """發送免費的回覆訊息 (Reply Message)"""
        async with AsyncApiClient(lineConfig) as apiClient:
            lineBotApi = AsyncMessagingApi(apiClient)
            await lineBotApi.reply_message(
                ReplyMessageRequest(
                    reply_token=replyToken,
                    messages=[TextMessage(text=text)]
                )
            )

    async def getOrCreateUser(self, lineUserId: str) -> User:
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
            # 重新載入以獲取 ID
            result = await self.db.execute(
                select(User).filter(User.lineUserId == lineUserId).options(selectinload(User.watchedStocks))
            )
            user = result.scalars().first()
        return user

    async def handleWatchStock(self, lineUserId: str, symbols: list, replyToken: str):
        """處理關注股票請求：建立關聯並回覆訊息"""
        user = await self.getOrCreateUser(lineUserId)
        successList = []
        errorList = []
        alreadyWatched = []
        
        for symbol in symbols:
            try:
                stockInfo = await self.stockCrawler.getOrCreateStockInfo(self.db, symbol)
                if not stockInfo:
                    errorList.append(symbol)
                    continue

                if stockInfo not in user.watchedStocks:
                    user.watchedStocks.append(stockInfo)
                    stockInfo.isWatched = True
                    successList.append(f"{stockInfo.name}({symbol})")
                    # 自動啟動背景爬取 - 暫時停用以節省資料庫容量
                    # asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))
                else:
                    alreadyWatched.append(symbol)
            except Exception as e:
                print(f"ERROR: [關注] {symbol} 失敗: {str(e)}")
                errorList.append(symbol)

        await self.db.commit()

        replyMsgs = []
        if successList:
            replyMsgs.append(f"✅ 關注成功！\n您已關注：{', '.join(successList)}\n系統將於每日 13:35 為您推送收盤報告。")
        
        if errorList:
            replyMsgs.append(f"❌ 輸入錯誤，股票不存在：{', '.join(errorList)}")

        if not successList and not errorList and alreadyWatched:
            replyMsgs.append("ℹ️ 提示：您輸入的股票已經在您的關注清單中囉！")

        if replyMsgs:
            await self.replyText(replyToken, "\n\n".join(replyMsgs))

    async def handleJoinStock(self, symbols: list, replyToken: str):
        """處理加入股票請求：僅啟動爬取並簡單回覆 - 暫時停用"""
        # for symbol in symbols:
        #     asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))
        
        await self.replyText(replyToken, f"ℹ️ 提示：目前已暫停歷史資料爬取功能以節省資源。\n您的指令 {', '.join(symbols)} 未被執行。")

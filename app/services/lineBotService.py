import re
import asyncio
from app.services.stockCrawler import StockCrawlerService
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class LineBotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 注意：crawler 現在會自己管理 Session，所以這裡不需要傳入 db
        self.stockCrawler = StockCrawlerService()

    async def handleMessage(self, event):
        """處理 Line 訊息事件 (僅在 Console 印出進度，不發送 Line 訊息)"""
        userMessage = event.message.text
        userId = event.source.user_id

        # 檢查是否為「股票 [代碼] [代碼]...」
        if userMessage.startswith("股票"):
            stockSymbols = re.findall(r'\d+', userMessage)
            
            if not stockSymbols:
                print("DEBUG: [Line] 收到指令但未偵測到數字代碼。")
                return

            print(f"DEBUG: [Line] 收到爬取請求：{', '.join(stockSymbols)} (User: {userId})")

            # 啟動背景任務，不再使用 replyToken 發送訊息
            for symbol in stockSymbols:
                # 使用 create_task 讓它在背景跑
                asyncio.create_task(self.stockCrawler.fetch10YearHistory(symbol))
        else:
            print(f"DEBUG: [Line] 收到非指令訊息：{userMessage}")

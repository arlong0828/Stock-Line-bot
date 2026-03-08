import twstock
import asyncio
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from app.models.stockData import User, StockInfo
from app.database.session import AsyncSessionLocal
from app.core.config import settings
from linebot.v3.messaging import (
    AsyncMessagingApi,
    AsyncApiClient,
    Configuration,
    TextMessage,
    PushMessageRequest
)
import logging

logger = logging.getLogger(__name__)
lineConfig = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

class ReportService:
    async def getDailyMarketReport(self):
        """獲取所有使用者的關注股票報告並推播至 Line"""
        async with AsyncSessionLocal() as db:
            # 1. 查詢所有有關注股票的使用者及其名單
            result = await db.execute(
                select(User).options(selectinload(User.watchedStocks))
            )
            users = result.scalars().all()

            if not users:
                print("DEBUG: [收盤報告] 資料庫中目前沒有使用者關注任何股票。")
                return

            print(f"DEBUG: [收盤報告] 開始為 {len(users)} 位使用者生成報告...")
            
            loop = asyncio.get_event_loop()
            
            async with AsyncApiClient(lineConfig) as apiClient:
                lineBotApi = AsyncMessagingApi(apiClient)

                for user in users:
                    reportMessages = []
                    
                    for stock in user.watchedStocks:
                        try:
                            # 獲取今日即時收盤資料
                            data = await loop.run_in_executor(None, twstock.realtime.get, stock.symbol)
                            
                            if data['success']:
                                realtime = data['realtime']
                                price = float(realtime['latest_trade_price'])
                                openPrice = float(realtime['open'])
                                
                                # 計算漲跌幅
                                change = price - openPrice
                                changePercent = (change / openPrice * 100) if openPrice != 0 else 0
                                
                                statusEmoji = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
                                etfTag = " [ETF]" if stock.is_etf else ""
                                
                                # 格式化訊息
                                msg = (
                                    f"股票名稱: {stock.name}{etfTag}\n"
                                    f"漲跌: {changePercent:+.2f}% {statusEmoji}\n"
                                    f"開盤價: {openPrice}\n"
                                    f"收盤價: {price}"
                                )
                                reportMessages.append(msg)
                            else:
                                print(f"ERROR: [報告] 抓取 {stock.symbol} 失敗")
                        except Exception as e:
                            print(f"ERROR: [報告] 處理 {stock.symbol} 時出錯: {str(e)}")

                    if reportMessages:
                        # 組合所有關注股票訊息為一則推播
                        fullReport = "📊 今日收盤報告 📊\n\n" + "\n\n---\n\n".join(reportMessages)
                        
                        try:
                            pushRequest = PushMessageRequest(
                                to=user.lineUserId,
                                messages=[TextMessage(text=fullReport)]
                            )
                            await lineBotApi.push_message(pushRequest)
                            print(f"DONE: [報告] 已發送至使用者 {user.lineUserId}")
                        except Exception as e:
                            print(f"ERROR: [報告] 發送 Line 訊息失敗: {str(e)}")

reportService = ReportService()

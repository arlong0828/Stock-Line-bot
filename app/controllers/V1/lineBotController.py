import re
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from app.core.config import settings
from app.services.lineBotService import LineBotService
from app.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
lineConfig = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

@router.get("/")
async def home():
    """根目錄路由實作"""
    return {"status": "running", "message": "Stock-Line-bot is alive!"}

@router.get("/breakout")
async def breakout(db: AsyncSession = Depends(get_db)):
    """手動查看目前資料庫計算出的飆股候選"""
    lineBotService = LineBotService(db)
    report = await lineBotService.handleBreakoutAnalysis(limit=5)
    return {"report": report}

@router.post("/webhook")
async def lineWebhook(
    request: Request,
    x_line_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """處理 Line Webhook 請求"""
    logger.info("--- 收到 Webhook 請求 ---")
    
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()
    body_str = body.decode("utf-8")
    
    try:
        lineBotService = LineBotService(db)
        events = handler.parser.parse(body_str, x_line_signature)

        async with AsyncApiClient(lineConfig) as apiClient:
            lineBotApi = AsyncMessagingApi(apiClient)

            for event in events:
                if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                    userMessage = event.message.text.strip()
                    responseText = None

                    # 判斷 1: 關注股票 (用於每日報告)
                    if userMessage.startswith("關注股票"):
                        stockSymbols = re.findall(r'\d+', userMessage)
                        if stockSymbols:
                            lineUserId = event.source.user_id
                            logger.info("偵測到關注指令：%s", stockSymbols)
                            await lineBotService.handleWatchStock(lineUserId, stockSymbols)
                            responseText = f"✅ 已加入關注：{' '.join(stockSymbols)}"

                    # 判斷 2: 加入股票 (用於歷史爬取)
                    elif userMessage.startswith("加入股票") or userMessage.startswith("股票"):
                        stockSymbols = re.findall(r'\d+', userMessage)
                        if stockSymbols:
                            print(f"DEBUG: [Controller] 偵測到「加入」指令：{stockSymbols}")
                            await lineBotService.handleJoinStock(stockSymbols)
                            responseText = f"⏳ 已開始背景抓取：{' '.join(stockSymbols)} 的歷史資料"

                    # 判斷 3: 飆股分析
                    elif userMessage.startswith("飆股"):
                        print("DEBUG: [Controller] 偵測到「飆股」指令")
                        responseText = await lineBotService.handleBreakoutAnalysis(limit=5)

                    else:
                        print(f"DEBUG: [Controller] 忽略非指令訊息：{userMessage}")
                        responseText = "可用指令：加入股票 2330、關注股票 2330、飆股"

                    if responseText:
                        replyRequest = ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=responseText)]
                        )
                        await lineBotApi.reply_message(replyRequest)

    except InvalidSignatureError:
        logger.error("Invalid Line Signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.exception("Webhook processing error")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    return {"status": "ok"}

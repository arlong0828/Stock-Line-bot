import re
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from app.core.config import settings
from app.services.lineBotService import LineBotService
from app.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@router.get("/")
async def home():
    """根目錄路由實作"""
    logger.info("收到健康檢查請求 (Root)")
    return {"status": "running", "message": "Stock-Line-bot is alive!"}

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
        
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                userMessage = event.message.text
                
                # --- 這是在 Controller 層級的兩個核心判斷 (Judgments) ---
                
                # 判斷 1: 關注股票 (用於每日報告)
                if userMessage.startswith("關注股票"):
                    stockSymbols = re.findall(r'\d+', userMessage)
                    if stockSymbols:
                        lineUserId = event.source.user_id
                        print(f"DEBUG: [Controller] 偵測到「關注」指令：{stockSymbols} (User: {lineUserId})")
                        await lineBotService.handleWatchStock(lineUserId, stockSymbols)
                
                # 判斷 2: 加入股票 (用於歷史爬取)
                elif userMessage.startswith("加入股票") or userMessage.startswith("股票"):
                    stockSymbols = re.findall(r'\d+', userMessage)
                    if stockSymbols:
                        print(f"DEBUG: [Controller] 偵測到「加入」指令：{stockSymbols}")
                        await lineBotService.handleJoinStock(stockSymbols)
                
                else:
                    print(f"DEBUG: [Controller] 忽略非指令訊息：{userMessage}")
                
    except InvalidSignatureError:
        logger.error("Invalid Line Signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}

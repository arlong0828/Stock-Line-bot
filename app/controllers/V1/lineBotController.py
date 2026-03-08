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

@router.post("/webhook")
async def lineWebhook(
    request: Request,
    x_line_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """處理 Line Webhook 請求"""
    # 立即印出日誌，確保連線有到
    logger.info("--- 收到 Webhook 請求 ---")
    
    if not x_line_signature:
        logger.warning("缺少 X-Line-Signature 標頭")
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()
    body_str = body.decode("utf-8")
    
    print(f"DEBUG: Signature: {x_line_signature}")
    print(f"DEBUG: Body: {body_str}")

    try:
        # 確保 handler 使用的是最新的 Secret
        handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        lineBotService = LineBotService(db)
        
        # 取得所有事件
        events = handler.parser.parse(body_str, x_line_signature)
        logger.info(f"收到 {len(events)} 個事件")
        
        for event in events:
            # 如果是 LINE Console 的 Verify 測試，這是一個 dummy 事件
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                # 處理訊息事件
                await lineBotService.handleMessage(event)
            else:
                logger.info(f"收到非訊息事件: {type(event)}")
                
    except InvalidSignatureError:
        logger.error(f"Invalid Line Signature! Secret used: {settings.LINE_CHANNEL_SECRET[:4]}...{settings.LINE_CHANNEL_SECRET[-4:]}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # 回報詳細錯誤，避免 LINE 回報 401 但其實是其他問題
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}

from fastapi import FastAPI
from app.controllers.V1 import lineBotController
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.reportService import reportService
from app.services.stockCrawler import stockCrawlerService
import logging
from contextlib import asynccontextmanager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立排程器
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 啟動時執行 ---
    logger.info("正在啟動定時任務...")
    
    # 1. 每日收盤報告：週一至週五 13:35 (純印出，不入庫)
    scheduler.add_job(
        reportService.getDailyMarketReport,
        trigger=CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
        id="daily_market_report",
        name="台股收盤報告",
        replace_existing=True
    )

    # 2. 每日資料自動入庫：週一至週五 14:30 (正式抓取最新 EOD 資料並存檔)
    scheduler.add_job(
        stockCrawlerService.updateAllStocksData,
        trigger=CronTrigger(day_of_week='mon-fri', hour=14, minute=30),
        id="daily_data_archive",
        name="收盤資料自動入庫",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("排程器已啟動 (13:35 報告, 14:30 入庫)")
    
    yield
    
    # --- 關閉時執行 ---
    logger.info("正在關閉排程器...")
    scheduler.shutdown()

app = FastAPI(title="Stock Line Bot API", lifespan=lifespan)

# 註冊路由
app.include_router(lineBotController.router)

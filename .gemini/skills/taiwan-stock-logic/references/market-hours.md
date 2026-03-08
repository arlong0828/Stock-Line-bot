# Market Hours Logic

此文件提供如何在程式碼中精確判斷台股交易日與市場狀態。

## 1. 判斷交易日 (Is Market Open?)

使用 `datetime` 判斷是否為週一至週五，並需額外排除國定假日。

```python
from datetime import datetime, time
import pytz

def is_market_day(dt: datetime) -> bool:
    # 轉換為台北時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    dt_taipei = dt.astimezone(taipei_tz)
    
    # 判斷週末 (5=Saturday, 6=Sunday)
    if dt_taipei.weekday() >= 5:
        return False
    
    # 國定假日邏輯 (建議維護一個清單或使用外部 API)
    # holidays = ["2026-01-01", "2026-02-17", ...]
    # if dt_taipei.strftime("%Y-%m-%d") in holidays:
    #     return False
    
    return True

def get_market_status(dt: datetime) -> str:
    taipei_tz = pytz.timezone('Asia/Taipei')
    dt_taipei = dt.astimezone(taipei_tz).time()
    
    if time(9, 0) <= dt_taipei <= time(13, 30):
        return "OPEN"
    elif dt_taipei < time(9, 0):
        return "PRE_MARKET"
    else:
        return "CLOSED"
```

## 2. 定時任務設定 (APScheduler)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone="Asia/Taipei")

# 每日收盤報告 (週一至週五 13:35)
scheduler.add_job(
    push_daily_report,
    trigger=CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
    id="daily_report"
)
```

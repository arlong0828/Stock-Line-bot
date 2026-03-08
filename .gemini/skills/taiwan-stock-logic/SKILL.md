---
name: taiwan-stock-logic
description: 台灣股市業務邏輯專家，處理開收盤時間、國定假日判斷、台股配色與 twstock 庫的整合。
---

# Taiwan Stock Logic Expert

此 Skill 指導如何處理台股特有的業務邏輯與時間規則，確保 Bot 的推播與查詢符合市場運行。

## 市場交易時間 (Market Hours)

台股市場運行時間（台北時間 UTC+8）：
- **交易日**：週一至週五（國定假日休市）。
- **開盤時間**：09:00。
- **收盤時間**：13:30。
- **盤後定價**：14:00 - 14:30。

### 邏輯判斷
- 使用 `datetime` 時務必轉換為 `Asia/Taipei` 時區。
- 參考 [market-hours.md](references/market-hours.md) 實作交易日與休市判斷邏輯。

## 台股配色慣例 (Color Conventions)

與美股相反，台股的顏色慣例為：
- **上漲**：紅色 (`#FF0000`)。
- **下跌**：綠色 (`#008000`) 或 藍色（視介面而定，Line Bot 推薦綠色）。
- **平盤**：灰色 (`#808080`) 或 白色。

## 常用程式庫實作 (twstock)

使用 `twstock` 抓取資料的非同步包裝建議：

```python
import twstock
import asyncio

async def fetch_realtime_data(symbol: str):
    # 由於 twstock 本身是同步的，建議在執行緒池中執行
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, twstock.realtime.get, symbol)
    return data
```

## 推播邏輯 (Push Notification)

- **開盤提醒** (09:00)：推播昨日收盤價或當前試撮。
- **收盤報告** (13:35)：推播今日最終表現與漲跌幅。
- **定時任務**：建議使用 `APScheduler` 並設定時區為 `Asia/Taipei`。

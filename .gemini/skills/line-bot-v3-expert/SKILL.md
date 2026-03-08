---
name: line-bot-v3-expert
description: Line Bot SDK v3 專家，提供 Webhook 處理、Signature 驗證、非同步訊息發送與 Flex Message 設計。
---

# Line Bot SDK v3 Expert

此 Skill 指導如何實作基於 Line Bot SDK v3 的非同步機器人，並整合至 FastAPI 專案。

## 基礎設定 (Configuration)

在 `app/core/config.py` 中應包含以下環境變數：
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`

## Webhook 實作流程

1. **路由定義**：
    - 使用 `APIRouter` 定義 `POST /webhook`。
    - 取得 `X-Line-Signature` 標頭。
2. **Signature 驗證**：
    - 使用 `WebhookHandler` 進行驗證。
3. **事件處理**：
    - 定義 `@handler.add(MessageEvent, message=TextMessageContent)` 處理函式。
    - **注意**：v3 使用非同步處理時，應使用 `AsyncWebhookHandler`。

## 非同步訊息發送

```python
from linebot.v3.messaging import (
    AsyncMessagingApi,
    AsyncApiClient,
    Configuration,
    TextMessage,
    PushMessageRequest
)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

async def send_text_message(user_id: str, text: str):
    async with AsyncApiClient(configuration) as api_client:
        line_bot_api = AsyncMessagingApi(api_client)
        text_message = TextMessage(text=text)
        push_message_request = PushMessageRequest(to=user_id, messages=[text_message])
        await line_bot_api.push_message(push_message_request)
```

## Flex Message 設計

- 優先從 `assets/flex-templates/` 讀取 JSON 模板。
- 使用 `FlexMessage` 與 `FlexContainer.from_json()` 載入自定義樣式。
- 參考 [flex-templates.md](references/flex-templates.md) 以取得常用的股票資訊版面。

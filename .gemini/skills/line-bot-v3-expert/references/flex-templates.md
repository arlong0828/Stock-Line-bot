# Flex Message Templates

此文件提供 Stock-Line-bot 專案中常用的 Flex Message 範本。

## 1. 股票資訊版面 (Stock Info)

這是一個精美的台股資訊版面範本，包含股價、漲跌幅、以及顏色標示（紅漲綠跌）。

```json
{
  "type": "bubble",
  "header": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "{stock_name} ({stock_symbol})",
        "weight": "bold",
        "size": "xl"
      }
    ]
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
          {
            "type": "text",
            "text": "{current_price}",
            "size": "3xl",
            "weight": "bold",
            "color": "{status_color}"
          },
          {
            "type": "text",
            "text": "{change_amount} ({change_percent}%)",
            "size": "md",
            "color": "{status_color}",
            "flex": 0
          }
        ]
      }
    ]
  }
}
```

## 使用範例

```python
import json
from linebot.v3.messaging import FlexMessage, FlexContainer

async def create_stock_flex(stock_data: dict):
    # status_color: 紅色 #FF0000 (漲), 綠色 #008000 (跌), 灰色 #808080 (平)
    template_str = get_template_from_file("stock-info.json")
    json_data = template_str.format(
        stock_name=stock_data["name"],
        stock_symbol=stock_data["symbol"],
        current_price=stock_data["price"],
        change_amount=stock_data["change"],
        change_percent=stock_data["change_percent"],
        status_color="#FF0000" if stock_data["change"] > 0 else "#008000"
    )
    return FlexMessage(
        alt_text=f"{stock_data['name']} 股價資訊",
        contents=FlexContainer.from_json(json_data)
    )
```

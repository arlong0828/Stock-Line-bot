# 📈 Taiwan Stock Line Bot (台股小幫手)

這是一個基於 **FastAPI** 實作的台股 Line 機器人，支援自動爬取 10 年歷史資料、每日收盤自動更新，以及個人化的關注股票每日收盤報告。

## 🌟 核心功能

- **歷史資料自動入庫**：輸入指令即可自動爬取並存入特定股票過去 10 年的每日交易數據。
- **每日收盤報告**：自動判斷台股收盤時間，於每個交易日 13:35 推播已關注股票的即時漲跌報告。
- **每日自動同步**：每天 14:30 自動同步資料庫中所有股票的最新收盤資訊，確保持續累積歷史數據。
- **智慧辨識**：自動區分一般股票與 ETF，並提供格式化的漲跌幅與 emoji 視覺提示。
- **高效能非同步架構**：採用非同步優先設計，爬取大量歷史資料時不影響 Line Bot 的正常回應。

## 🛠 技術棧

- **網頁框架**: FastAPI (Python 3.11)
- **資料庫**: SQLite (支援非同步 aiosqlite)
- **ORM**: SQLAlchemy 2.0 (Async mode)
- **遷移工具**: Alembic
- **Line SDK**: Line Bot SDK v3 (Asynchronous)
- **資料來源**: `twstock` (證交所/櫃買中心資料)
- **定時任務**: APScheduler

## 🚀 快速開始

### 1. 環境設定
確保你已安裝 Python 3.11，並建立虛擬環境：
```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境變數
建立 `.env` 檔案並填入你的金鑰：
```env
LINE_CHANNEL_ACCESS_TOKEN=你的_TOKEN
LINE_CHANNEL_SECRET=你的_SECRET
DATABASE_URL=sqlite+aiosqlite:///./stock_bot.db
```

### 3. 資料庫初始化
```bash
python -m alembic upgrade head
```

### 4. 啟動伺服器
```bash
python -m uvicorn app.main:app --reload
```

## 📱 Line Bot 指令

| 指令範例 | 功能描述 |
| :--- | :--- |
| `加入股票 2330 0050` | 啟動背景任務，自動爬取這些股票近 10 年的歷史資料。 |
| `關注股票 2330` | 將股票加入你的個人關注清單，每日收盤後會收到推播報告。 |

## 📁 專案架構

```text
├── app/
│   ├── controllers/    # 路由處理 (Webhook 與 API)
│   ├── core/           # 系統設定 (Config)
│   ├── database/       # 資料庫連線管理
│   ├── models/         # SQLAlchemy 資料模型
│   ├── schemas/        # Pydantic 資料驗證
│   ├── services/       # 業務邏輯 (爬蟲、報告、Line 服務)
│   └── main.py         # 程式進入點與定時任務設定
├── alembic/            # 資料庫遷移歷史
└── .env                # 機密資訊檔案
```

## 📝 開發規範

- 採用 **camelCase** (小駝峰) 命名變數、函式與檔案。
- 嚴格遵守 `Controller -> Service -> Model` 階層式架構。
- 所有資料庫操作必須支援非同步 (`async/await`)。

---
*本專案僅供學習與研究使用，不構成任何投資建議。*

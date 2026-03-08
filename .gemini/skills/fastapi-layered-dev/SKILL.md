---
name: fastapi-layered-dev
description: FastAPI 階層式架構專家，專注於 Schema -> Service -> Model 的分離與非同步操作。
---

# FastAPI Layered Development

此 Skill 指導如何在 FastAPI 專案中實作嚴謹的「階層式架構」，確保業務邏輯與資料持久化層完全分離。

## 階層定義 (Layer Definitions)

### 1. Models Layer (`app/models/`)
- **職責**：定義 SQLAlchemy 資料庫結構。
- **規則**：僅包含資料表定義與關聯。不要在此處編寫業務邏輯或驗證。
- **參考範例**：見 [layer-patterns.md](references/layer-patterns.md) 中的 Models 區段。

### 2. Schemas Layer (`app/schemas/`)
- **職責**：定義 Pydantic 資料驗證模型 (DTOs)。
- **規則**：區分 `Create` (輸入)、`Read` (輸出) 與 `Update` 結構。所有 API 請求與回應必須通過 Schema。
- **參考範例**：見 [layer-patterns.md](references/layer-patterns.md) 中的 Schemas 區段。

### 3. Services Layer (`app/services/`)
- **職責**：封裝業務邏輯與資料庫操作。
- **規則**：
    - 接收 Schema 物件或基礎類型作為輸入。
    - 使用 `async/await` 進行非同步資料庫查詢（透過 `AsyncSession`）。
    - 處理例外狀況與邊界情況。
    - 回傳 Pydantic 模型或 Python 基礎類型。
- **參考範例**：見 [layer-patterns.md](references/layer-patterns.md) 中的 Services 區段。

### 4. API/Router Layer (`app/api/` 或 `app/controllers/`)
- **職責**：處理 HTTP 請求、解析參數、呼叫 Service 並回傳回應。
- **規則**：Router 應保持極度簡潔（不超過 10 行邏輯），所有繁重工作委託給 Service。

## 非同步開發規範 (Async Guidelines)

- 始終使用 `async def` 定義函式。
- 使用 `await` 呼叫資料庫 session 或外部 API。
- 嚴禁在非同步函式中使用阻塞型庫（如 `requests`，應改用 `httpx`）。

## 常用工作流

1. **新增資源**：
    - 先建立 `models/resource.py`。
    - 接著建立 `schemas/resource.py`。
    - 實作 `services/resource_service.py` 中的 CRUD 邏輯。
    - 最後在 `api/v1/endpoints/resource.py` 暴露路徑。

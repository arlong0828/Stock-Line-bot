from fastapi import FastAPI
from app.controllers.V1 import lineBotController

app = FastAPI(title="Stock Line Bot API")

# 註冊路由
app.include_router(lineBotController.router, tags=["Line Bot"])

@app.get("/")
async def home():
    return {"status": "running", "message": "Stock-Line-bot is alive!"}

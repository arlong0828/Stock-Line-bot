from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# 強制重新載入 .env 檔案內容 (本地端開發用)
load_dotenv(override=True)

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Stock Line Bot"
    
    # Line Bot Settings
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    
    # Database Settings
    # 如果環境變數中有 DATABASE_URL 則優先使用 (Render 會提供)
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./stock_bot.db")

    # Render/Neon 部署輔助：確保使用 postgresql+asyncpg:// 並移除不相容參數
    @property
    def asyncDatabaseUrl(self) -> str:
        url = self.DATABASE_URL
        if not url:
            return ""
        
        # 1. 移除不相容的 SSL 查詢參數 (asyncpg 不支援 sslmode)
        if "?" in url:
            url = url.split("?")[0]

        # 2. 替換協定開頭
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

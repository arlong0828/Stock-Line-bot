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

    # Render 部署輔助：如果 URL 以 postgres:// 開頭，改為 postgresql+asyncpg://
    @property
    def asyncDatabaseUrl(self) -> str:
        url = self.DATABASE_URL
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

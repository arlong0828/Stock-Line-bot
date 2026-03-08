from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# 強制重新載入 .env 檔案內容
load_dotenv(override=True)

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Stock Line Bot"
    
    # Line Bot Settings
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    
    # Database Settings
    # 這裡我們直接從 os.environ 讀取，並加上預設值
    DATABASE_URL: str = os.environ.get("DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

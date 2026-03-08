from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 使用非同步引擎 (關閉 SQL 日誌)
engine = create_async_engine(
    settings.asyncDatabaseUrl,
    echo=False,
    future=True
)

# 使用 AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 關鍵修正：必須呼叫 declarative_base() 來生成 Base 類別
Base = declarative_base()

async def get_db():
    """FastAPI Depends 用的資料庫連線生成器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

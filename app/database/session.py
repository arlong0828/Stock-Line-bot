from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 優化連線池設定以支援大量背景爬蟲
engine = create_async_engine(
    settings.asyncDatabaseUrl,
    echo=False,
    future=True,
    pool_size=20,         # 增加基礎連線數
    max_overflow=10,      # 增加允許的溢位連線數
    pool_recycle=300,     # 每 5 分鐘回收連線，防止被雲端資料庫斷線
    pool_pre_ping=True    # 每次連線前先測試是否可用
)

# 使用 AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """FastAPI Depends 用的資料庫連線生成器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

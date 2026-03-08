from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# --- 動態偵測與設定連線池 ---
# 如果是 SQLite，不能帶 pool_size 等參數；如果是 Postgres，則需要優化
dbUrl = settings.asyncDatabaseUrl
isSqlite = dbUrl.startswith("sqlite")

if isSqlite:
    # SQLite 設定：輕量、不使用連線池
    engine = create_async_engine(
        dbUrl,
        echo=False,
        future=True
    )
    logger.info("DEBUG: [資料庫] 目前運行於 本地端 (SQLite) 模式")
else:
    # Postgres (Render/Neon) 設定：高效能連線池
    engine = create_async_engine(
        dbUrl,
        echo=False,
        future=True,
        pool_size=10,         # 雲端模式保留 10 個連線
        max_overflow=20,      # 支援突發的高流量
        pool_recycle=300,     # 防止被雲端平台斷線
        pool_pre_ping=True
    )
    logger.info("DEBUG: [資料庫] 目前運行於 雲端 (Postgres) 模式")

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

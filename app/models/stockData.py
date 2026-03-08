from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, Index, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

# 多對多關聯表：使用者關注哪些股票
userWatchedStocks = Table(
    "user_watched_stocks",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("stock_id", Integer, ForeignKey("stock_info.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    lineUserId = Column(String(50), unique=True, index=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯到關注的股票
    watchedStocks = relationship("StockInfo", secondary=userWatchedStocks, back_populates="watchedBy")

class StockInfo(Base):
    __tablename__ = "stock_info"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=True)
    is_etf = Column(Boolean, default=False)
    isWatched = Column(Boolean, default=False) # 系統級關注標記
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    histories = relationship("StockHistory", back_populates="stock_info", cascade="all, delete-orphan")
    # 關聯到關注的使用者
    watchedBy = relationship("User", secondary=userWatchedStocks, back_populates="watchedStocks")

class StockHistory(Base):
    __tablename__ = "stock_histories"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock_info.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stock_info = relationship("StockInfo", back_populates="histories")

    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uix_stock_id_date'),
        Index('idx_stock_id_date', 'stock_id', 'date'),
    )

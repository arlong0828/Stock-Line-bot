from sqlalchemy import Column, Integer ,String, Float , Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class StockInfo(Base):
    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, index = True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    histories = relationship("StockHistory", back_populates="stock_info", cascade="all, delete-orphan")

class StockHistory(Base):
    __tablename__ = "stock_histories"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stock_info.id"), nullable = False)
    date = Column(Date, nullable=False, index= True)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stock_info = relationship("StockInfo" , back_populates="histories")
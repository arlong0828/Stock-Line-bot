# Layer Patterns Reference

此文件提供 Stock-Line-bot 專案中各層級的標準範本。

## 1. Models Layer (`app/models/stock.py`)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database.session import Base

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    last_price = Column(Float)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

## 2. Schemas Layer (`app/schemas/stock.py`)

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    symbol: str
    name: str

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    name: Optional[str] = None
    last_price: Optional[float] = None

class StockRead(StockBase):
    id: int
    last_price: Optional[float]
    updated_at: datetime

    class Config:
        from_attributes = True
```

## 3. Services Layer (`app/services/stock_service.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.stock import Stock
from app.schemas.stock import StockCreate

async def get_stock_by_symbol(db: AsyncSession, symbol: str):
    result = await db.execute(select(Stock).filter(Stock.symbol == symbol))
    return result.scalars().first()

async def create_stock(db: AsyncSession, stock_in: StockCreate):
    db_obj = Stock(**stock_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
```

## 4. API/Router Layer (`app/api/v1/stock.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.stock import StockRead, StockCreate
from app.services import stock_service

router = APIRouter()

@router.post("/", response_model=StockRead)
async def create_stock(stock_in: StockCreate, db: AsyncSession = Depends(get_db)):
    db_stock = await stock_service.get_stock_by_symbol(db, stock_in.symbol)
    if db_stock:
        raise HTTPException(status_code=400, detail="Stock already exists")
    return await stock_service.create_stock(db, stock_in)
```

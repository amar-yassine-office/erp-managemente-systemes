from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. ASSET ALLOCATION SCHEMAS
# =====================================================================

class AssetAllocationCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    target_stocks_pct: Decimal = Field(..., ge=0, le=100)
    target_bonds_pct: Decimal = Field(..., ge=0, le=100)
    target_cash_pct: Decimal = Field(..., ge=0, le=100)


class AssetAllocationUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    target_stocks_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    target_bonds_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    target_cash_pct: Optional[Decimal] = Field(None, ge=0, le=100)


class AssetAllocationOutSchema(BaseModel):
    id: int
    name: str
    target_stocks_pct: Decimal
    target_bonds_pct: Decimal
    target_cash_pct: Decimal

    class Config:
        from_attributes = True


# =====================================================================
# 2. PORTFOLIO SCHEMAS
# =====================================================================

class PortfolioCreateSchema(BaseModel):
    strategy_id: Optional[int] = Field(None)
    account_number: str = Field(..., max_length=30)
    name: str = Field(..., max_length=150)
    status: Optional[str] = Field("ACTIVE")
    cash_balance: Optional[Decimal] = Field(Decimal("0.0000"), ge=0)
    total_value: Optional[Decimal] = Field(Decimal("0.0000"), ge=0)


class PortfolioUpdateSchema(BaseModel):
    strategy_id: Optional[int] = Field(None)
    name: Optional[str] = Field(None, max_length=150)
    status: Optional[str] = Field(None)
    cash_balance: Optional[Decimal] = Field(None, ge=0)
    total_value: Optional[Decimal] = Field(None, ge=0)


class PortfolioOutSchema(BaseModel):
    id: int
    user_id: int
    strategy_id: Optional[int]
    account_number: str
    name: str
    status: str
    cash_balance: Decimal
    total_value: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 3. PORTFOLIO POSITION SCHEMAS
# =====================================================================

class PortfolioPositionCreateSchema(BaseModel):
    portfolio_id: int
    symbol: str = Field(..., max_length=20)
    quantity: Decimal
    average_buy_price: Decimal = Field(..., ge=0)
    current_price: Decimal = Field(..., ge=0)


class PortfolioPositionUpdateSchema(BaseModel):
    quantity: Optional[Decimal] = Field(None)
    average_buy_price: Optional[Decimal] = Field(None, ge=0)
    current_price: Optional[Decimal] = Field(None, ge=0)


class PortfolioPositionOutSchema(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 4. PORTFOLIO PERFORMANCE SCHEMAS
# =====================================================================

class PortfolioPerformanceCreateSchema(BaseModel):
    portfolio_id: int
    date: date
    nav_value: Decimal
    daily_return_pct: Optional[Decimal] = Field(Decimal("0.0000"))


class PortfolioPerformanceUpdateSchema(BaseModel):
    nav_value: Optional[Decimal] = Field(None)
    daily_return_pct: Optional[Decimal] = Field(None)


class PortfolioPerformanceOutSchema(BaseModel):
    id: int
    portfolio_id: int
    date: date
    nav_value: Decimal
    daily_return_pct: Decimal

    class Config:
        from_attributes = True
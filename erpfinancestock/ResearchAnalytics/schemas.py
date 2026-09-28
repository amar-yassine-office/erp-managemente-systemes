from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. MARKET ASSET SCHEMAS
# =====================================================================

class MarketAssetCreateSchema(BaseModel):
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    asset_class: str = Field("EQUITY")
    sector: Optional[str] = Field("", max_length=100)
    exchange: Optional[str] = Field("", max_length=50)
    is_active: Optional[bool] = True


class MarketAssetUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    asset_class: Optional[str] = Field(None)
    sector: Optional[str] = Field(None, max_length=100)
    exchange: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class MarketAssetOutSchema(BaseModel):
    id: int
    symbol: str
    name: str
    asset_class: str
    sector: str
    exchange: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 2. RESEARCH REPORT SCHEMAS
# =====================================================================

class ResearchReportCreateSchema(BaseModel):
    asset_id: Optional[int] = Field(None)
    title: str = Field(..., max_length=255)
    summary: str
    content: str
    status: Optional[str] = Field("DRAFT")
    is_premium: Optional[bool] = False
    published_at: Optional[datetime] = None


class ResearchReportUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = Field(None)
    is_premium: Optional[bool] = None
    published_at: Optional[datetime] = None


class ResearchReportOutSchema(BaseModel):
    id: int
    author_id: Optional[int]
    asset_id: Optional[int]
    title: str
    summary: str
    content: str
    status: str
    is_premium: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 3. ANALYST RECOMMENDATION SCHEMAS
# =====================================================================

class AnalystRecommendationCreateSchema(BaseModel):
    asset_id: int
    report_id: Optional[int] = None
    rating: str
    current_price_at_rating: Decimal = Field(..., ge=0)
    target_price: Decimal = Field(..., ge=0)
    time_horizon_months: Optional[int] = Field(12)
    is_active: Optional[bool] = True


class AnalystRecommendationUpdateSchema(BaseModel):
    rating: Optional[str] = None
    current_price_at_rating: Optional[Decimal] = Field(None, ge=0)
    target_price: Optional[Decimal] = Field(None, ge=0)
    time_horizon_months: Optional[int] = None
    is_active: Optional[bool] = None


class AnalystRecommendationOutSchema(BaseModel):
    id: int
    analyst_id: int
    asset_id: int
    report_id: Optional[int]
    rating: str
    current_price_at_rating: Decimal
    target_price: Decimal
    time_horizon_months: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 4. FINANCIAL METRIC SCHEMAS
# =====================================================================

class FinancialMetricCreateSchema(BaseModel):
    asset_id: int
    period_date: date
    pe_ratio: Optional[Decimal] = Field(None)
    pb_ratio: Optional[Decimal] = Field(None)
    eps: Optional[Decimal] = Field(None)
    debt_to_equity: Optional[Decimal] = Field(None)
    roe_pct: Optional[Decimal] = Field(None)
    free_cash_flow: Optional[Decimal] = Field(None)


class FinancialMetricUpdateSchema(BaseModel):
    pe_ratio: Optional[Decimal] = Field(None)
    pb_ratio: Optional[Decimal] = Field(None)
    eps: Optional[Decimal] = Field(None)
    debt_to_equity: Optional[Decimal] = Field(None)
    roe_pct: Optional[Decimal] = Field(None)
    free_cash_flow: Optional[Decimal] = Field(None)


class FinancialMetricOutSchema(BaseModel):
    id: int
    asset_id: int
    period_date: date
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    eps: Optional[Decimal]
    debt_to_equity: Optional[Decimal]
    roe_pct: Optional[Decimal]
    free_cash_flow: Optional[Decimal]

    class Config:
        from_attributes = True


# =====================================================================
# 5. MARKET SENTIMENT SCHEMAS
# =====================================================================

class MarketSentimentCreateSchema(BaseModel):
    asset_id: int
    sentiment_score: Decimal = Field(..., ge=-1.00, le=1.00)
    label: str
    news_source_count: Optional[int] = Field(0)
    summary: Optional[str] = Field("")


class MarketSentimentUpdateSchema(BaseModel):
    sentiment_score: Optional[Decimal] = Field(None, ge=-1.00, le=1.00)
    label: Optional[str] = None
    news_source_count: Optional[int] = None
    summary: Optional[str] = None


class MarketSentimentOutSchema(BaseModel):
    id: int
    asset_id: int
    sentiment_score: Decimal
    label: str
    news_source_count: int
    summary: str
    evaluated_at: datetime

    class Config:
        from_attributes = True
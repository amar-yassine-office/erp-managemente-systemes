from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. RISK LIMIT SCHEMAS
# =====================================================================

class RiskLimitCreateSchema(BaseModel):
    portfolio_id: int
    limit_type: str = Field(..., max_length=30)
    threshold_value: Decimal = Field(...)
    is_active: Optional[bool] = True


class RiskLimitUpdateSchema(BaseModel):
    threshold_value: Optional[Decimal] = Field(None)
    is_active: Optional[bool] = None


class RiskLimitOutSchema(BaseModel):
    id: int
    portfolio_id: int
    limit_type: str
    threshold_value: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 2. PORTFOLIO RISK METRIC SCHEMAS
# =====================================================================

class PortfolioRiskMetricCreateSchema(BaseModel):
    portfolio_id: int
    calculation_date: date
    var_95_daily: Optional[Decimal] = Field(None)
    var_99_daily: Optional[Decimal] = Field(None)
    expected_shortfall: Optional[Decimal] = Field(None)
    sharpe_ratio: Optional[Decimal] = Field(None)
    sortino_ratio: Optional[Decimal] = Field(None)
    beta: Optional[Decimal] = Field(None)
    volatility_annualized: Optional[Decimal] = Field(None)
    max_drawdown_pct: Optional[Decimal] = Field(None)


class PortfolioRiskMetricOutSchema(BaseModel):
    id: int
    portfolio_id: int
    calculation_date: date
    var_95_daily: Optional[Decimal]
    var_99_daily: Optional[Decimal]
    expected_shortfall: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    sortino_ratio: Optional[Decimal]
    beta: Optional[Decimal]
    volatility_annualized: Optional[Decimal]
    max_drawdown_pct: Optional[Decimal]

    class Config:
        from_attributes = True


# =====================================================================
# 3. STRESS TEST SCENARIO SCHEMAS
# =====================================================================

class StressTestScenarioCreateSchema(BaseModel):
    name: str = Field(..., max_length=150)
    description: str
    market_shock_pct: Decimal = Field(...)
    interest_rate_change_bps: Optional[int] = Field(0)


class StressTestScenarioUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    market_shock_pct: Optional[Decimal] = Field(None)
    interest_rate_change_bps: Optional[int] = None


class StressTestScenarioOutSchema(BaseModel):
    id: int
    name: str
    description: str
    market_shock_pct: Decimal
    interest_rate_change_bps: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 4. STRESS TEST RESULT SCHEMAS
# =====================================================================

class StressTestResultCreateSchema(BaseModel):
    scenario_id: int
    portfolio_id: int
    projected_loss_amount: Decimal = Field(...)
    projected_loss_pct: Decimal = Field(...)


class StressTestResultOutSchema(BaseModel):
    id: int
    scenario_id: int
    portfolio_id: int
    projected_loss_amount: Decimal
    projected_loss_pct: Decimal
    evaluated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 5. RISK ALERT SCHEMAS
# =====================================================================

class RiskAlertCreateSchema(BaseModel):
    portfolio_id: int
    risk_limit_id: Optional[int] = None
    title: str = Field(..., max_length=255)
    description: str
    severity: Optional[str] = Field("MEDIUM")
    status: Optional[str] = Field("OPEN")


class RiskAlertUpdateSchema(BaseModel):
    status: Optional[str] = Field(None)
    resolved_at: Optional[datetime] = Field(None)


class RiskAlertOutSchema(BaseModel):
    id: int
    portfolio_id: int
    risk_limit_id: Optional[int]
    title: str
    description: str
    severity: str
    status: str
    acknowledged_by_id: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
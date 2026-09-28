from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. CLEARING HOUSE SCHEMAS
# =====================================================================

class ClearingHouseCreateSchema(BaseModel):
    name: str = Field(..., max_length=150, example="Depository Trust & Clearing Corporation")
    code: str = Field(..., max_length=20, example="DTCC")
    country: str = Field(..., max_length=100, example="United States")
    is_active: Optional[bool] = Field(True)


class ClearingHouseUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = Field(None)


class ClearingHouseOutSchema(BaseModel):
    id: int
    name: str
    code: str
    country: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 2. CLEARING MEMBER ACCOUNT SCHEMAS
# =====================================================================

class ClearingMemberAccountCreateSchema(BaseModel):
    clearing_house_id: int = Field(..., description="ID of the parent Clearing House")
    account_number: str = Field(..., max_length=50, example="DTCC-ACC-9988")
    account_name: str = Field(..., max_length=150, example="Primary Equities Clearing Account")
    balance: Decimal = Field(Decimal("0.0000"), ge=0, example="1500000.0000")
    currency: str = Field("USD", max_length=3, example="USD")
    is_active: Optional[bool] = Field(True)


class ClearingMemberAccountUpdateSchema(BaseModel):
    account_name: Optional[str] = Field(None, max_length=150)
    balance: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = Field(None)


class ClearingMemberAccountOutSchema(BaseModel):
    id: int
    clearing_house_id: int
    account_number: str
    account_name: str
    balance: Decimal
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


# =====================================================================
# 3. TRADE SETTLEMENT SCHEMAS
# =====================================================================

class TradeSettlementCreateSchema(BaseModel):
    trade_id: str = Field(..., max_length=100, example="TRD-2026-99128")
    clearing_house_id: int = Field(..., description="Clearing House ID")
    clearing_account_id: int = Field(..., description="Clearing Member Account ID")
    user_id: int = Field(..., description="User ID associated with the settlement")
    symbol: str = Field(..., max_length=20, example="AAPL")
    quantity: Decimal = Field(..., example="500.0000")
    price: Decimal = Field(..., example="175.5000")
    total_amount: Decimal = Field(..., example="87750.0000")
    settlement_type: str = Field("DVP", example="DVP", description="DVP, FOP, or RVP")
    status: str = Field("PENDING", example="PENDING", description="PENDING, SETTLED, FAILED, or CANCELLED")
    trade_date: datetime = Field(..., example="2026-09-24T10:30:00Z")
    settlement_date: date = Field(..., example="2026-09-25")
    actual_settlement_time: Optional[datetime] = Field(None)


class TradeSettlementUpdateSchema(BaseModel):
    status: Optional[str] = Field(None, description="PENDING, SETTLED, FAILED, or CANCELLED")
    actual_settlement_time: Optional[datetime] = Field(None)


class TradeSettlementOutSchema(BaseModel):
    id: int
    trade_id: str
    clearing_house_id: int
    clearing_account_id: int
    user_id: int
    symbol: str
    quantity: Decimal
    price: Decimal
    total_amount: Decimal
    settlement_type: str
    status: str
    trade_date: datetime
    settlement_date: date
    actual_settlement_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 4. MARGIN REQUIREMENT SCHEMAS
# =====================================================================

class MarginRequirementCreateSchema(BaseModel):
    clearing_account_id: int = Field(..., description="Clearing Member Account ID")
    initial_margin: Decimal = Field(..., example="250000.0000")
    maintenance_margin: Decimal = Field(..., example="200000.0000")
    collateral_posted: Decimal = Field(..., example="275000.0000")
    margin_call_amount: Decimal = Field(Decimal("0.0000"), example="0.0000")
    is_margin_call_active: Optional[bool] = Field(False)


class MarginRequirementUpdateSchema(BaseModel):
    initial_margin: Optional[Decimal] = Field(None)
    maintenance_margin: Optional[Decimal] = Field(None)
    collateral_posted: Optional[Decimal] = Field(None)
    margin_call_amount: Optional[Decimal] = Field(None)
    is_margin_call_active: Optional[bool] = Field(None)


class MarginRequirementOutSchema(BaseModel):
    id: int
    clearing_account_id: int
    initial_margin: Decimal
    maintenance_margin: Decimal
    collateral_posted: Decimal
    margin_call_amount: Decimal
    is_margin_call_active: bool
    last_updated: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 5. SETTLEMENT RECONCILIATION SCHEMAS
# =====================================================================

class SettlementReconciliationCreateSchema(BaseModel):
    settlement_id: int = Field(..., description="Trade Settlement ID linked to the break")
    break_type: str = Field(..., example="AMOUNT_MISMATCH", description="AMOUNT_MISMATCH, QUANTITY_MISMATCH, MISSING_INTERNAL, or MISSING_CLEARING")
    description: str = Field(..., example="Internal ledger states $87,750.00, whereas DTCC report indicates $87,800.00.")
    status: Optional[str] = Field("OPEN", example="OPEN", description="OPEN, INVESTIGATING, or RESOLVED")


class SettlementReconciliationUpdateSchema(BaseModel):
    status: Optional[str] = Field(None, description="OPEN, INVESTIGATING, or RESOLVED")
    description: Optional[str] = Field(None)


class SettlementReconciliationOutSchema(BaseModel):
    id: int
    settlement_id: int
    break_type: str
    description: str
    status: str
    resolved_by_id: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
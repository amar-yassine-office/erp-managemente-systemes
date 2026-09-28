from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. FISCAL YEAR SCHEMAS
# =====================================================================

class FiscalYearCreateSchema(BaseModel):
    name: str = Field(..., max_length=50)
    start_date: date
    end_date: date
    is_closed: Optional[bool] = False


class FiscalYearUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_closed: Optional[bool] = None


class FiscalYearOutSchema(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_closed: bool

    class Config:
        from_attributes = True


# =====================================================================
# 2. ACCOUNT SCHEMAS
# =====================================================================

class AccountCreateSchema(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=150)
    account_type: str = Field(..., max_length=20)
    parent_id: Optional[int] = None
    is_active: Optional[bool] = True
    description: Optional[str] = ""


class AccountUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    account_type: Optional[str] = Field(None, max_length=20)
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AccountOutSchema(BaseModel):
    id: int
    code: str
    name: str
    account_type: str
    parent_id: Optional[int]
    is_active: bool
    description: str

    class Config:
        from_attributes = True


# =====================================================================
# 3. JOURNAL ENTRY SCHEMAS
# =====================================================================

class JournalEntryItemCreateSchema(BaseModel):
    account_id: int
    debit: Optional[Decimal] = Field(Decimal('0.0000'))
    credit: Optional[Decimal] = Field(Decimal('0.0000'))
    memo: Optional[str] = Field("", max_length=255)


class JournalEntryItemOutSchema(BaseModel):
    id: int
    account_id: int
    debit: Decimal
    credit: Decimal
    memo: str

    class Config:
        from_attributes = True


class JournalEntryCreateSchema(BaseModel):
    entry_number: str = Field(..., max_length=50)
    fiscal_year_id: int
    date: date
    description: str
    status: Optional[str] = Field("DRAFT")
    items: List[JournalEntryItemCreateSchema]


class JournalEntryUpdateSchema(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = None
    status: Optional[str] = None


class JournalEntryOutSchema(BaseModel):
    id: int
    entry_number: str
    fiscal_year_id: int
    date: date
    description: str
    status: str
    created_by_id: Optional[int]
    posted_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    items: List[JournalEntryItemOutSchema]

    class Config:
        from_attributes = True


# =====================================================================
# 4. TAX RATE SCHEMAS
# =====================================================================

class TaxRateCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    rate: Decimal = Field(...)
    account_id: int
    is_active: Optional[bool] = True


class TaxRateUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    rate: Optional[Decimal] = None
    account_id: Optional[int] = None
    is_active: Optional[bool] = None


class TaxRateOutSchema(BaseModel):
    id: int
    name: str
    rate: Decimal
    account_id: int
    is_active: bool

    class Config:
        from_attributes = True


# =====================================================================
# 5. INVOICE SCHEMAS
# =====================================================================

class InvoiceItemCreateSchema(BaseModel):
    account_id: int
    description: str = Field(..., max_length=255)
    quantity: Optional[Decimal] = Field(Decimal('1.0000'))
    unit_price: Decimal = Field(...)
    tax_rate_id: Optional[int] = None


class InvoiceItemOutSchema(BaseModel):
    id: int
    account_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate_id: Optional[int]
    line_total: Decimal

    class Config:
        from_attributes = True


class InvoiceCreateSchema(BaseModel):
    invoice_number: str = Field(..., max_length=50)
    invoice_type: str = Field(..., max_length=20)
    user_id: int
    issue_date: date
    due_date: date
    notes: Optional[str] = ""
    items: List[InvoiceItemCreateSchema]


class InvoiceUpdateSchema(BaseModel):
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceOutSchema(BaseModel):
    id: int
    invoice_number: str
    invoice_type: str
    user_id: int
    issue_date: date
    due_date: date
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemOutSchema]

    class Config:
        from_attributes = True


# =====================================================================
# 6. PAYMENT SCHEMAS
# =====================================================================

class PaymentCreateSchema(BaseModel):
    payment_reference: str = Field(..., max_length=100)
    invoice_id: int
    payment_account_id: int
    amount: Decimal = Field(...)
    payment_date: date
    payment_method: str = Field(..., max_length=30)
    memo: Optional[str] = ""


class PaymentOutSchema(BaseModel):
    id: int
    payment_reference: str
    invoice_id: int
    payment_account_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    memo: str
    created_at: datetime

    class Config:
        from_attributes = True
from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
from .models import (
    FiscalYear,
    Account,
    JournalEntry,
    TaxRate,
    Invoice,
    Payment,
)
from .schemas import (
    FiscalYearCreateSchema,
    FiscalYearUpdateSchema,
    FiscalYearOutSchema,
    AccountCreateSchema,
    AccountUpdateSchema,
    AccountOutSchema,
    JournalEntryCreateSchema,
    JournalEntryUpdateSchema,
    JournalEntryOutSchema,
    TaxRateCreateSchema,
    TaxRateOutSchema,
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    InvoiceOutSchema,
    PaymentCreateSchema,
    PaymentOutSchema,
)
from .service import AccountingFinanceService

# =====================================================================
# 1. FISCAL YEAR ENDPOINTS
# =====================================================================

@router.post("/fiscal-years/", response={201: FiscalYearOutSchema})
def create_fiscal_year(request, payload: FiscalYearCreateSchema):
    return 201, AccountingFinanceService.create_fiscal_year(data=payload)

@router.get("/fiscal-years/", response=List[FiscalYearOutSchema])
def list_fiscal_years(request):
    return AccountingFinanceService.list_fiscal_years()

@router.patch("/fiscal-years/{fy_id}/", response=FiscalYearOutSchema)
def update_fiscal_year(request, fy_id: int, payload: FiscalYearUpdateSchema):
    return AccountingFinanceService.update_fiscal_year(fy_id=fy_id, data=payload)


# =====================================================================
# 2. ACCOUNT ENDPOINTS
# =====================================================================

@router.post("/accounts/", response={201: AccountOutSchema})
def create_account(request, payload: AccountCreateSchema):
    return 201, AccountingFinanceService.create_account(data=payload)

@router.get("/accounts/", response=List[AccountOutSchema])
def list_accounts(request, account_type: Optional[str] = Query(None)):
    return AccountingFinanceService.list_accounts(account_type=account_type)

@router.patch("/accounts/{account_id}/", response=AccountOutSchema)
def update_account(request, account_id: int, payload: AccountUpdateSchema):
    return AccountingFinanceService.update_account(account_id=account_id, data=payload)


# =====================================================================
# 3. JOURNAL ENTRY ENDPOINTS
# =====================================================================

@router.post("/journal-entries/", response={201: JournalEntryOutSchema})
def create_journal_entry(request, payload: JournalEntryCreateSchema):
    return 201, AccountingFinanceService.create_journal_entry(user=request.user, data=payload)

@router.get("/journal-entries/", response=List[JournalEntryOutSchema])
def list_journal_entries(request, status: Optional[str] = Query(None), fiscal_year_id: Optional[int] = Query(None)):
    return AccountingFinanceService.list_journal_entries(status=status, fiscal_year_id=fiscal_year_id)

@router.patch("/journal-entries/{entry_id}/", response=JournalEntryOutSchema)
def update_journal_entry(request, entry_id: int, payload: JournalEntryUpdateSchema):
    return AccountingFinanceService.update_journal_entry(entry_id=entry_id, user=request.user, data=payload)


# =====================================================================
# 4. TAX RATE ENDPOINTS
# =====================================================================

@router.post("/tax-rates/", response={201: TaxRateOutSchema})
def create_tax_rate(request, payload: TaxRateCreateSchema):
    return 201, AccountingFinanceService.create_tax_rate(data=payload)

@router.get("/tax-rates/", response=List[TaxRateOutSchema])
def list_tax_rates(request):
    return AccountingFinanceService.list_tax_rates()


# =====================================================================
# 5. INVOICE ENDPOINTS
# =====================================================================

@router.post("/invoices/", response={201: InvoiceOutSchema})
def create_invoice(request, payload: InvoiceCreateSchema):
    return 201, AccountingFinanceService.create_invoice(data=payload)

@router.get("/invoices/", response=List[InvoiceOutSchema])
def list_invoices(request, invoice_type: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    return AccountingFinanceService.list_invoices(invoice_type=invoice_type, status=status)


# =====================================================================
# 6. PAYMENT ENDPOINTS
# =====================================================================

@router.post("/payments/", response={201: PaymentOutSchema})
def create_payment(request, payload: PaymentCreateSchema):
    return 201, AccountingFinanceService.create_payment(data=payload)

@router.get("/payments/", response=List[PaymentOutSchema])
def list_payments(request):
    return AccountingFinanceService.list_payments()
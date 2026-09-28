from decimal import Decimal
from typing import Optional
from django.db import transaction

# Import Celery tasks
from .tasks import (
    post_journal_entry_task,
    process_invoice_payment_task,
    generate_financial_statement_task,
    close_fiscal_year_task,
)
from .models import JournalEntry, Invoice, Payment, FiscalYear


class AccountingFinanceService:

    @staticmethod
    def post_journal_entry_async(journal_entry_id: int, user_id: int):
        """Triggers asynchronous journal entry posting and validation."""
        task = post_journal_entry_task.delay(journal_entry_id, user_id)
        return {"task_id": task.id, "message": "Journal entry posting initiated in background."}

    @staticmethod
    def record_payment_and_process_async(
        payment_reference: str,
        invoice_id: int,
        payment_account_id: int,
        amount: Decimal,
        payment_date,
        payment_method: str,
        memo: str = ""
    ):
        """Creates a payment record and dispatches background processing."""
        with transaction.atomic():
            payment = Payment.objects.create(
                payment_reference=payment_reference,
                invoice_id=invoice_id,
                payment_account_id=payment_account_id,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                memo=memo,
            )

        # Dispatch Celery task to update invoice status and generate GL entries
        task = process_invoice_payment_task.delay(payment.id)
        return {
            "payment_id": payment.id,
            "task_id": task.id,
            "message": "Payment recorded. Background invoice reconciliation started."
        }

    @staticmethod
    def request_financial_statement_async(fiscal_year_id: int):
        """Triggers financial statement aggregation report in background."""
        task = generate_financial_statement_task.delay(fiscal_year_id)
        return {"task_id": task.id, "message": "Financial statement generation queued."}

    @staticmethod
    def close_fiscal_year_async(fiscal_year_id: int):
        """Triggers background fiscal year closing."""
        task = close_fiscal_year_task.delay(fiscal_year_id)
        return {"task_id": task.id, "message": "Fiscal year closure queued."}

    #the operation on the models 
from typing import List, Optional
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import (
    FiscalYear,
    Account,
    JournalEntry,
    JournalEntryItem,
    TaxRate,
    Invoice,
    InvoiceItem,
    Payment,
)
from .schemas import (
    FiscalYearCreateSchema,
    FiscalYearUpdateSchema,
    AccountCreateSchema,
    AccountUpdateSchema,
    JournalEntryCreateSchema,
    JournalEntryUpdateSchema,
    TaxRateCreateSchema,
    TaxRateUpdateSchema,
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    PaymentCreateSchema,
)

User = get_user_model()


class AccountingFinanceService:

    # --- Fiscal Year ---
    @classmethod
    @transaction.atomic
    def create_fiscal_year(cls, data: FiscalYearCreateSchema) -> FiscalYear:
        return FiscalYear.objects.create(**data.dict())

    @staticmethod
    def list_fiscal_years() -> List[FiscalYear]:
        return FiscalYear.objects.all()

    @classmethod
    @transaction.atomic
    def update_fiscal_year(cls, fy_id: int, data: FiscalYearUpdateSchema) -> FiscalYear:
        fy = get_object_or_404(FiscalYear, id=fy_id)
        for k, v in data.dict(exclude_unset=True).items():
            setattr(fy, k, v)
        fy.save()
        return fy

    # --- Account ---
    @classmethod
    @transaction.atomic
    def create_account(cls, data: AccountCreateSchema) -> Account:
        payload = data.dict()
        parent_id = payload.pop("parent_id", None)
        parent = Account.objects.get(id=parent_id) if parent_id else None
        return Account.objects.create(parent=parent, **payload)

    @staticmethod
    def list_accounts(account_type: Optional[str] = None) -> List[Account]:
        qs = Account.objects.all()
        if account_type:
            qs = qs.filter(account_type=account_type)
        return qs

    @classmethod
    @transaction.atomic
    def update_account(cls, account_id: int, data: AccountUpdateSchema) -> Account:
        acc = get_object_or_404(Account, id=account_id)
        payload = data.dict(exclude_unset=True)
        if "parent_id" in payload:
            pid = payload.pop("parent_id")
            acc.parent = Account.objects.get(id=pid) if pid else None
        for k, v in payload.items():
            setattr(acc, k, v)
        acc.save()
        return acc

    # --- Journal Entry ---
    @classmethod
    @transaction.atomic
    def create_journal_entry(cls, user: User, data: JournalEntryCreateSchema) -> JournalEntry:
        fy = get_object_or_404(FiscalYear, id=data.fiscal_year_id)
        items_data = data.items
        
        entry = JournalEntry.objects.create(
            entry_number=data.entry_number,
            fiscal_year=fy,
            date=data.date,
            description=data.description,
            status=data.status,
            created_by=user,
            posted_by=user if data.status == 'POSTED' else None
        )

        for item in items_data:
            account = get_object_or_404(Account, id=item.account_id)
            JournalEntryItem.objects.create(
                journal_entry=entry,
                account=account,
                debit=item.debit,
                credit=item.credit,
                memo=item.memo
            )

        entry.full_clean()
        entry.save()
        return entry

    @staticmethod
    def list_journal_entries(status: Optional[str] = None, fiscal_year_id: Optional[int] = None) -> List[JournalEntry]:
        qs = JournalEntry.objects.prefetch_related("items__account").all()
        if status:
            qs = qs.filter(status=status)
        if fiscal_year_id:
            qs = qs.filter(fiscal_year_id=fiscal_year_id)
        return qs

    @classmethod
    @transaction.atomic
    def update_journal_entry(cls, entry_id: int, user: User, data: JournalEntryUpdateSchema) -> JournalEntry:
        entry = get_object_or_404(JournalEntry, id=entry_id)
        payload = data.dict(exclude_unset=True)
        
        if "status" in payload and payload["status"] == 'POSTED' and entry.status != 'POSTED':
            entry.posted_by = user

        for k, v in payload.items():
            setattr(entry, k, v)
        
        entry.full_clean()
        entry.save()
        return entry

    # --- Tax Rate ---
    @classmethod
    @transaction.atomic
    def create_tax_rate(cls, data: TaxRateCreateSchema) -> TaxRate:
        payload = data.dict()
        account_id = payload.pop("account_id")
        account = get_object_or_404(Account, id=account_id)
        return TaxRate.objects.create(account=account, **payload)

    @staticmethod
    def list_tax_rates() -> List[TaxRate]:
        return TaxRate.objects.select_related("account").all()

    # --- Invoice ---
    @classmethod
    @transaction.analytic if hasattr(transaction, 'analytic') else transaction.atomic
    def create_invoice(cls, data: InvoiceCreateSchema) -> Invoice:
        target_user = get_object_or_404(User, id=data.user_id)
        items_data = data.items

        invoice = Invoice.objects.create(
            invoice_number=data.invoice_number,
            invoice_type=data.invoice_type,
            user=target_user,
            issue_date=data.issue_date,
            due_date=data.due_date,
            notes=data.notes,
        )

        subtotal = Decimal('0.0000')
        tax_amount = Decimal('0.0000')

        for item in items_data:
            account = get_object_or_404(Account, id=item.account_id)
            tax_rate = get_object_or_404(TaxRate, id=item.tax_rate_id) if item.tax_rate_id else None
            
            line_total = item.quantity * item.unit_price
            subtotal += line_total

            item_tax = Decimal('0.0000')
            if tax_rate:
                item_tax = line_total * (tax_rate.rate / Decimal('100.00'))
                tax_amount += item_tax

            InvoiceItem.objects.create(
                invoice=invoice,
                account=account,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=tax_rate,
                line_total=line_total
            )

        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount
        invoice.save()
        return invoice

    @staticmethod
    def list_invoices(invoice_type: Optional[str] = None, status: Optional[str] = None) -> List[Invoice]:
        qs = Invoice.objects.prefetch_related("items__account", "items__tax_rate").all()
        if invoice_type:
            qs = qs.filter(invoice_type=invoice_type)
        if status:
            qs = qs.filter(status=status)
        return qs

    # --- Payment ---
    @classmethod
    @transaction.atomic
    def create_payment(cls, data: PaymentCreateSchema) -> Payment:
        invoice = get_object_or_404(Invoice, id=data.invoice_id)
        account = get_object_or_404(Account, id=data.payment_account_id)
        
        payment = Payment.objects.create(
            payment_reference=data.payment_reference,
            invoice=invoice,
            payment_account=account,
            amount=data.amount,
            payment_date=data.payment_date,
            payment_method=data.payment_method,
            memo=data.memo
        )
        return payment

    @staticmethod
    def list_payments() -> List[Payment]:
        return Payment.objects.select_related("invoice", "payment_account").all()
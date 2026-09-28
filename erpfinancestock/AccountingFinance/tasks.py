from decimal import Decimal
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Invoice, Payment, JournalEntry, JournalEntryItem, FiscalYear, Account


@shared_task
def post_journal_entry_task(journal_entry_id: int, user_id: int):
    """
    Asynchronously posts a draft JournalEntry, verifying double-entry balance,
    fiscal year status, and line items.
    """
    with transaction.atomic():
        try:
            entry = JournalEntry.objects.select_for_update().get(id=journal_entry_id)
            if entry.status == 'POSTED':
                return f"JournalEntry #{entry.entry_number} is already posted."

            # Perform validations defined in model clean()
            entry.status = 'POSTED'
            entry.posted_by_id = user_id
            entry.clean()
            entry.save()

            return f"JournalEntry #{entry.entry_number} posted successfully."
        except JournalEntry.DoesNotExist:
            return f"JournalEntry ID {journal_entry_id} not found."
        except ValidationError as e:
            return f"Validation failed for JournalEntry ID {journal_entry_id}: {e.messages}"


@shared_task
def process_invoice_payment_task(payment_id: int):
    """
    Asynchronously processes a payment, creates corresponding journal entries,
    and updates invoice payment status (PAID or PARTIALLY_PAID).
    """
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().select_related('invoice', 'payment_account').get(id=payment_id)
            invoice = payment.invoice

            # 1. Calculate total paid so far
            total_paid = sum(p.amount for p in invoice.payments.all())

            # 2. Update Invoice Status
            if total_paid >= invoice.total_amount:
                invoice.status = 'PAID'
            elif total_paid > Decimal('0.0000'):
                invoice.status = 'PARTIALLY_PAID'
            invoice.save(update_fields=['status'])

            # 3. Auto-generate General Ledger Journal Entry for Payment
            fiscal_year = FiscalYear.objects.filter(
                start_date__lte=payment.payment_date,
                end_date__gte=payment.payment_date,
                is_closed=False
            ).first()

            if fiscal_year:
                entry_number = f"JE-PAY-{payment.payment_reference}"
                entry, created = JournalEntry.objects.get_or_create(
                    entry_number=entry_number,
                    defaults={
                        'fiscal_year': fiscal_year,
                        'date': payment.payment_date,
                        'description': f"Automated entry for Payment #{payment.payment_reference}",
                        'status': 'POSTED',
                    }
                )

                if created:
                    # Debit Payment Account (e.g. Bank/Cash), Credit Receivable/Payable Account
                    JournalEntryItem.objects.create(
                        journal_entry=entry,
                        account=payment.payment_account,
                        debit=payment.amount if invoice.invoice_type == 'CUSTOMER' else Decimal('0.0000'),
                        credit=payment.amount if invoice.invoice_type == 'VENDOR' else Decimal('0.0000'),
                        memo=f"Payment for Invoice #{invoice.invoice_number}"
                    )

            return f"Payment #{payment.payment_reference} processed. Invoice status updated to {invoice.status}."

        except Payment.DoesNotExist:
            return f"Payment ID {payment_id} not found."


@shared_task
def generate_financial_statement_task(fiscal_year_id: int):
    """
    Calculates General Ledger totals for Assets, Liabilities, Equity, Revenue,
    and Expenses for a specific fiscal year.
    """
    try:
        fy = FiscalYear.objects.get(id=fiscal_year_id)
        items = JournalEntryItem.objects.filter(
            journal_entry__fiscal_year=fy,
            journal_entry__status='POSTED'
        ).select_related('account')

        totals = {'ASSET': 0, 'LIABILITY': 0, 'EQUITY': 0, 'REVENUE': 0, 'EXPENSE': 0}
        for item in items:
            acc_type = item.account.account_type
            totals[acc_type] += (item.debit - item.credit)

        return {
            'fiscal_year': fy.name,
            'summary': {k: str(v) for k, v in totals.items()}
        }
    except FiscalYear.DoesNotExist:
        return f"FiscalYear ID {fiscal_year_id} not found."


@shared_task
def close_fiscal_year_task(fiscal_year_id: int):
    """
    Closes a fiscal year to prevent any further journal entry postings.
    """
    try:
        fy = FiscalYear.objects.get(id=fiscal_year_id)
        fy.is_closed = True
        fy.save(update_fields=['is_closed'])
        return f"Fiscal Year {fy.name} successfully closed."
    except FiscalYear.DoesNotExist:
        return f"Fiscal Year ID {fiscal_year_id} not found."
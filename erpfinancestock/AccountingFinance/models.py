from django.db import models

# Create your models here.
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FiscalYear(models.Model):
    """Tracks accounting periods and closing states."""

    name = models.CharField(max_length=50, unique=True, help_text="e.g. FY 2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(
        default=False, help_text="Closed fiscal years block new journal entries."
    )

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({'Closed' if self.is_closed else 'Open'})"


class Account(models.Model):
    """General Ledger Chart of Accounts (Assets, Liabilities, Equity, Revenue, Expenses)."""

    ACCOUNT_TYPES = (
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    )

    code = models.CharField(
        max_length=20, unique=True, db_index=True, help_text="e.g., 1010 for Cash"
    )
    name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent account for hierarchical chart of accounts.",
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} [{self.get_account_type_display()}]"


class JournalEntry(models.Model):
    """Header record for a general ledger transaction."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('CANCELLED', 'Cancelled'),
    )

    entry_number = models.CharField(max_length=50, unique=True, db_index=True)
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.PROTECT, related_name='journal_entries'
    )
    date = models.DateField(db_index=True)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_journal_entries',
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_journal_entries',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Journal {self.entry_number} ({self.date}) [{self.status}]"

    def clean(self):
        """Enforces balanced double-entry accounting (Debits == Credits) upon posting."""
        if self.status == 'POSTED':
            if self.fiscal_year and self.fiscal_year.is_closed:
                raise ValidationError("Cannot post entries to a closed fiscal year.")

            items = self.items.all()
            if not items.exists():
                raise ValidationError("Journal entry must have at least two line items.")

            total_debit = sum(item.debit for item in items)
            total_credit = sum(item.credit for item in items)

            if total_debit != total_credit:
                raise ValidationError(
                    f"Unbalanced entry! Total Debits ({total_debit}) must equal Total Credits ({total_credit})."
                )


class JournalEntryItem(models.Model):
    """Line items for double-entry ledger postings."""

    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name='items'
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='journal_items'
    )
    debit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.0000'))
    credit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.0000'))
    memo = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("A line item cannot contain both a Debit and a Credit amount.")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Line item must specify either a Debit or Credit amount.")

    def __str__(self):
        return f"{self.account.code} - Dr: {self.debit} | Cr: {self.credit}"


class TaxRate(models.Model):
    """Tax configurations (e.g., VAT, Sales Tax)."""

    name = models.CharField(max_length=100)
    rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Percentage rate, e.g. 19.00 for 19%"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='tax_rates',
        help_text="Liability/Expense account for tax collection/payment",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class Invoice(models.Model):
    """Accounts Receivable (Customer Invoices) and Accounts Payable (Vendor Bills)."""

    INVOICE_TYPES = (
        ('CUSTOMER', 'Customer Invoice (AR)'),
        ('VENDOR', 'Vendor Bill (AP)'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued / Approved'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    )

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Customer or Vendor associated with this invoice",
    )

    issue_date = models.DateField()
    due_date = models.DateField()

    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.0000'))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.0000'))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('0.0000'))

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"Invoice #{self.invoice_number} ({self.get_invoice_type_display()}) - {self.total_amount}"


class InvoiceItem(models.Model):
    """Individual product/service line items on an invoice."""

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='items'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoice_items',
        help_text="Revenue account for sales or Expense account for bills",
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('1.0000'))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4)
    tax_rate = models.ForeignKey(
        TaxRate, on_delete=models.SET_NULL, null=True, blank=True
    )
    line_total = models.DecimalField(max_digits=18, decimal_places=4)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


class Payment(models.Model):
    """Tracks cash receipts and vendor disbursements applied against invoices."""

    PAYMENT_METHODS = (
        ('BANK_TRANSFER', 'Bank Wire Transfer'),
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CASH', 'Cash'),
    )

    payment_reference = models.CharField(max_length=100, unique=True)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name='payments'
    )
    payment_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='payments_processed',
        help_text="Bank or Cash account receiving/sending the funds",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    payment_date = models.DateField(db_index=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    memo = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.payment_reference} - {self.amount}"
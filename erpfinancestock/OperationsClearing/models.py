from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class ClearingHouse(models.Model):
    """Central Clearing House entity (e.g., DTCC, Euroclear, LCH)."""

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. DTCC, NSCC, EUROCLEAR")
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClearingMemberAccount(models.Model):
    """Firm's operational clearing account maintained at a Clearing House."""

    clearing_house = models.ForeignKey(
        ClearingHouse,
        on_delete=models.CASCADE,
        related_name='member_accounts',
    )
    account_number = models.CharField(max_length=50, unique=True)
    account_name = models.CharField(max_length=150)
    balance = models.DecimalField(max_digits=18, decimal_places=4, default=0.0000)
    currency = models.CharField(max_length=3, default='USD')

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.account_name} - {self.clearing_house.code} ({self.account_number})"


class TradeSettlement(models.Model):
    """Tracks the clearing and settlement life-cycle for trade executions (T+1 / T+2)."""

    SETTLEMENT_STATUS = (
        ('PENDING', 'Pending Settlement'),
        ('SETTLED', 'Settled Successfully'),
        ('FAILED', 'Settlement Failed'),
        ('CANCELLED', 'Cancelled'),
    )

    SETTLEMENT_TYPE = (
        ('DVP', 'Delivery Versus Payment'),
        ('FOP', 'Free of Payment'),
        ('RVP', 'Receive Versus Payment'),
    )

    trade_id = models.CharField(max_length=100, unique=True, db_index=True)
    clearing_house = models.ForeignKey(
        ClearingHouse,
        on_delete=models.PROTECT,
        related_name='settlements',
    )
    clearing_account = models.ForeignKey(
        ClearingMemberAccount,
        on_delete=models.PROTECT,
        related_name='settlements',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_settlements',
    )

    symbol = models.CharField(max_length=20, db_index=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    price = models.DecimalField(max_digits=18, decimal_places=4)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4)

    settlement_type = models.CharField(max_length=10, choices=SETTLEMENT_TYPE, default='DVP')
    status = models.CharField(max_length=20, choices=SETTLEMENT_STATUS, default='PENDING', db_index=True)

    trade_date = models.DateTimeField()
    settlement_date = models.DateField(db_index=True)
    actual_settlement_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-trade_date']

    def __str__(self):
        return f"Settlement #{self.trade_id} - {self.symbol} [{self.status}]"


class MarginRequirement(models.Model):
    """Tracks collateral and margin accounts managed by clearing operations."""

    clearing_account = models.ForeignKey(
        ClearingMemberAccount,
        on_delete=models.CASCADE,
        related_name='margin_requirements',
    )
    initial_margin = models.DecimalField(max_digits=18, decimal_places=4)
    maintenance_margin = models.DecimalField(max_digits=18, decimal_places=4)
    collateral_posted = models.DecimalField(max_digits=18, decimal_places=4)
    margin_call_amount = models.DecimalField(max_digits=18, decimal_places=4, default=0.0000)

    is_margin_call_active = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Margin Requirement - {self.clearing_account.account_number}"


class SettlementReconciliation(models.Model):
    """Logs breaks, mismatches, and reconciliation audit steps between internal records and clearing reports."""

    BREAK_TYPES = (
        ('AMOUNT_MISMATCH', 'Amount Mismatch'),
        ('QUANTITY_MISMATCH', 'Quantity Mismatch'),
        ('MISSING_INTERNAL', 'Trade Missing Internally'),
        ('MISSING_CLEARING', 'Trade Missing at Clearing House'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open Discrepancy'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
    )

    settlement = models.ForeignKey(
        TradeSettlement,
        on_delete=models.CASCADE,
        related_name='reconciliations',
    )
    break_type = models.CharField(max_length=30, choices=BREAK_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reconciliations',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Break #{self.id} ({self.get_break_type_display()}) - {self.status}"
    
from django.db import models

# Create your models here.
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AssetAllocation(models.Model):
    """Defines target asset distribution strategy (e.g., Aggressive, Balanced)."""

    name = models.CharField(max_length=100)
    target_stocks_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    target_bonds_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    target_cash_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    """Core portfolio model owned directly by a Django User."""

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
    )

    # Linked directly to Django's standard User model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolios',
    )
    strategy = models.ForeignKey(
        AssetAllocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='portfolios',
    )

    account_number = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ACTIVE'
    )

    # Financial Summary Fields
    cash_balance = models.DecimalField(
        max_digits=18, decimal_places=4, default=Decimal('0.0000')
    )
    total_value = models.DecimalField(
        max_digits=18, decimal_places=4, default=Decimal('0.0000')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.account_number})'


class PortfolioPosition(models.Model):
    """Tracks current stock/asset holdings inside a specific portfolio."""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='positions'
    )

    symbol = models.CharField(max_length=20)  # e.g., AAPL, NVDA, TSLA
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    average_buy_price = models.DecimalField(max_digits=15, decimal_places=4)
    current_price = models.DecimalField(max_digits=15, decimal_places=4)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('portfolio', 'symbol')

    def __str__(self):
        return f'{self.portfolio.account_number} - {self.symbol}'


class PortfolioPerformance(models.Model):
    """Historical record for tracking portfolio NAV and daily returns."""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='performance_records'
    )
    date = models.DateField()
    nav_value = models.DecimalField(max_digits=18, decimal_places=4)
    daily_return_pct = models.DecimalField(
        max_digits=7, decimal_places=4, default=Decimal('0.0000')
    )

    class Meta:
        ordering = ['-date']
        unique_together = ('portfolio', 'date')

    def __str__(self):
        return f'{self.portfolio.account_number} - {self.date}'
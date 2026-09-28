from django.db import models

# Create your models here.
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MarketAsset(models.Model):
    """Tracks tradable assets, market data, and sector categories."""

    ASSET_CLASSES = (
        ('EQUITY', 'Equity / Stock'),
        ('BOND', 'Fixed Income / Bond'),
        ('COMMODITY', 'Commodity'),
        ('CRYPTO', 'Cryptocurrency'),
        ('FX', 'Foreign Exchange'),
    )

    symbol = models.CharField(max_length=20, unique=True, db_index=True)  # e.g., NVDA, AAPL
    name = models.CharField(max_length=200)
    asset_class = models.CharField(
        max_length=20, choices=ASSET_CLASSES, default='EQUITY'
    )
    sector = models.CharField(max_length=100, blank=True)  # e.g., Technology, Healthcare
    exchange = models.CharField(max_length=50, blank=True)  # e.g., NASDAQ, NYSE
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class ResearchReport(models.Model):
    """Stores detailed equity research, valuation reports, and market analyses."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('REVIEW', 'Under Review'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='research_reports',
    )
    asset = models.ForeignKey(
        MarketAsset,
        on_delete=models.CASCADE,
        related_name='research_reports',
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()  # Full report text / Markdown
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='DRAFT'
    )
    is_premium = models.BooleanField(default=False)  # For institutional clients only

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class AnalystRecommendation(models.Model):
    """Tracks analyst ratings and target price projections for specific stocks."""

    RATING_CHOICES = (
        ('STRONG_BUY', 'Strong Buy'),
        ('BUY', 'Buy'),
        ('HOLD', 'Hold'),
        ('SELL', 'Sell'),
        ('STRONG_SELL', 'Strong Sell'),
    )

    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    asset = models.ForeignKey(
        MarketAsset,
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    report = models.ForeignKey(
        ResearchReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations',
    )

    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    current_price_at_rating = models.DecimalField(max_digits=15, decimal_places=4)
    target_price = models.DecimalField(max_digits=15, decimal_places=4)
    time_horizon_months = models.PositiveIntegerField(default=12)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.asset.symbol} - {self.rating} by {self.analyst.username}"


class FinancialMetric(models.Model):
    """Stores fundamental financial indicators for asset evaluation (P/E, EPS, Debt/Equity)."""

    asset = models.ForeignKey(
        MarketAsset, on_delete=models.CASCADE, related_name='financial_metrics'
    )
    period_date = models.DateField()  # Quarterly / Annual ending date

    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pb_ratio = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    eps = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    debt_to_equity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    roe_pct = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    free_cash_flow = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    class Meta:
        unique_together = ('asset', 'period_date')
        ordering = ['-period_date']

    def __str__(self):
        return f"{self.asset.symbol} Metrics ({self.period_date})"


class MarketSentiment(models.Model):
    """Tracks news, social media sentiment, and market indicators for an asset."""

    SENTIMENT_CHOICES = (
        ('BULLISH', 'Bullish'),
        ('NEUTRAL', 'Neutral'),
        ('BEARISH', 'Bearish'),
    )

    asset = models.ForeignKey(
        MarketAsset, on_delete=models.CASCADE, related_name='sentiments'
    )
    sentiment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(-1.00), MaxValueValidator(1.00)],
        help_text="Score from -1.0 (Extremely Bearish) to +1.0 (Extremely Bullish)",
    )
    label = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    news_source_count = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True)

    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"{self.asset.symbol} - {self.label} ({self.sentiment_score})"
    
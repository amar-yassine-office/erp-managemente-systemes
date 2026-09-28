from django.db import models

# Create your models here.
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RiskLimit(models.Model):
    """Sets risk thresholds and limits for portfolios (e.g., max drawdown, VaR limit, sector concentration)."""

    LIMIT_TYPES = (
        ('MAX_DRAWDOWN', 'Maximum Drawdown (%)'),
        ('VAR_LIMIT', 'Value at Risk (VaR) Limit ($)'),
        ('CONCENTRATION', 'Single Asset Concentration (%)'),
        ('LEVERAGE', 'Maximum Leverage Ratio'),
    )

    portfolio = models.ForeignKey(
        'PortfolioManagement.Portfolio',
        on_delete=models.CASCADE,
        related_name='risk_limits',
    )
    limit_type = models.CharField(max_length=30, choices=LIMIT_TYPES)
    threshold_value = models.DecimalField(max_digits=18, decimal_places=4)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('portfolio', 'limit_type')

    def __str__(self):
        return f"{self.portfolio.account_number} - {self.get_limit_type_display()}: {self.threshold_value}"


class PortfolioRiskMetric(models.Model):
    """Stores calculated statistical risk indicators for portfolios."""

    portfolio = models.ForeignKey(
        'PortfolioManagement.Portfolio',
        on_delete=models.CASCADE,
        related_name='risk_metrics',
    )
    calculation_date = models.DateField()

    # Value at Risk (VaR) & Expected Shortfall (CVaR)
    var_95_daily = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        help_text="95% Confidence 1-Day Value at Risk ($)"
    )
    var_99_daily = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        help_text="99% Confidence 1-Day Value at Risk ($)"
    )
    expected_shortfall = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        help_text="Conditional VaR (CVaR)"
    )

    # Volatility & Ratio Metrics
    sharpe_ratio = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    sortino_ratio = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    beta = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    volatility_annualized = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    max_drawdown_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('portfolio', 'calculation_date')
        ordering = ['-calculation_date']

    def __str__(self):
        return f"{self.portfolio.account_number} Risk Metrics ({self.calculation_date})"


class StressTestScenario(models.Model):
    """Defines macroeconomic stress test conditions (e.g., 2008 Crash, Tech Selloff)."""

    name = models.CharField(max_length=150)
    description = models.TextField()
    market_shock_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Broad market shock percentage (e.g., -20.00 for a 20% crash)",
    )
    interest_rate_change_bps = models.IntegerField(
        default=0, help_text="Interest rate shift in basis points (e.g., +100 bps)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StressTestResult(models.Model):
    """Logs stress test simulation results on specific portfolios."""

    scenario = models.ForeignKey(
        StressTestScenario, on_delete=models.CASCADE, related_name='test_results'
    )
    portfolio = models.ForeignKey(
        'PortfolioManagement.Portfolio', on_delete=models.CASCADE, related_name='stress_test_results'
    )

    projected_loss_amount = models.DecimalField(max_digits=18, decimal_places=4)
    projected_loss_pct = models.DecimalField(max_digits=7, decimal_places=4)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"{self.portfolio.account_number} - {self.scenario.name}: -{self.projected_loss_pct}%"


class RiskAlert(models.Model):
    """Triggers automated alerts when portfolio metrics breach defined RiskLimits."""

    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    )

    portfolio = models.ForeignKey(
        'PortfolioManagement.Portfolio', on_delete=models.CASCADE, related_name='risk_alerts'
    )
    risk_limit = models.ForeignKey(
        RiskLimit, on_delete=models.SET_NULL, null=True, blank=True, related_name='triggered_alerts'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_risk_alerts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.portfolio.account_number} - {self.title}"
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    PortfolioRiskMetric,
    RiskAlert,
    RiskLimit,
    StressTestResult,
    StressTestScenario,
)


class RiskLimitInline(admin.TabularInline):
    model = RiskLimit
    extra = 0


class RiskAlertInline(admin.TabularInline):
    model = RiskAlert
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('title', 'severity', 'status', 'created_at')


@admin.register(RiskLimit)
class RiskLimitAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'limit_type', 'threshold_value', 'is_active', 'updated_at')
    list_filter = ('limit_type', 'is_active')
    search_fields = ('portfolio__account_number',)


@admin.register(PortfolioRiskMetric)
class PortfolioRiskMetricAdmin(admin.ModelAdmin):
    list_display = (
        'portfolio',
        'calculation_date',
        'var_95_daily',
        'sharpe_ratio',
        'beta',
        'max_drawdown_pct',
    )
    list_filter = ('calculation_date',)
    search_fields = ('portfolio__account_number',)
    date_hierarchy = 'calculation_date'


@admin.register(StressTestScenario)
class StressTestScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'market_shock_pct', 'interest_rate_change_bps', 'created_at')


@admin.register(StressTestResult)
class StressTestResultAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'scenario', 'projected_loss_amount', 'projected_loss_pct', 'evaluated_at')
    list_filter = ('scenario', 'evaluated_at')
    search_fields = ('portfolio__account_number',)


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'portfolio', 'severity', 'status', 'acknowledged_by', 'created_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('portfolio__account_number', 'title', 'description')
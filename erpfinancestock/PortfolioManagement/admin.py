from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import AssetAllocation, Portfolio, PortfolioPerformance, PortfolioPosition


@admin.register(AssetAllocation)
class AssetAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'target_stocks_pct',
        'target_bonds_pct',
        'target_cash_pct',
    )
    search_fields = ('name',)


class PortfolioPositionInline(admin.TabularInline):
    model = PortfolioPosition
    extra = 1
    fields = ('symbol', 'quantity', 'average_buy_price', 'current_price')


class PortfolioPerformanceInline(admin.TabularInline):
    model = PortfolioPerformance
    extra = 0
    readonly_fields = ('date', 'nav_value', 'daily_return_pct')
    can_delete = False
    max_num = 5


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = (
        'account_number',
        'name',
        'user',
        'strategy',
        'status',
        'cash_balance',
        'total_value',
        'created_at',
    )
    list_filter = ('status', 'strategy', 'created_at')
    search_fields = (
        'account_number',
        'name',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PortfolioPositionInline, PortfolioPerformanceInline]

    fieldsets = (
        (
            'Basic Information',
            {'fields': ('account_number', 'name', 'user', 'status')},
        ),
        ('Strategy & Allocation', {'fields': ('strategy',)}),
        ('Financials', {'fields': ('cash_balance', 'total_value')}),
        (
            'Timestamps',
            {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)},
        ),
    )


@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = (
        'portfolio',
        'symbol',
        'quantity',
        'average_buy_price',
        'current_price',
        'updated_at',
    )
    list_filter = ('symbol', 'updated_at')
    search_fields = ('portfolio__account_number', 'symbol')


@admin.register(PortfolioPerformance)
class PortfolioPerformanceAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'date', 'nav_value', 'daily_return_pct')
    list_filter = ('date',)
    search_fields = ('portfolio__account_number',)
    date_hierarchy = 'date'
    

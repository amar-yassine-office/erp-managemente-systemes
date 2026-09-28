from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    ClearingHouse,
    ClearingMemberAccount,
    MarginRequirement,
    SettlementReconciliation,
    TradeSettlement,
)


@admin.register(ClearingHouse)
class ClearingHouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'code')


@admin.register(ClearingMemberAccount)
class ClearingMemberAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'account_name', 'clearing_house', 'balance', 'currency', 'is_active')
    list_filter = ('clearing_house', 'currency', 'is_active')
    search_fields = ('account_number', 'account_name')


@admin.register(TradeSettlement)
class TradeSettlementAdmin(admin.ModelAdmin):
    list_display = (
        'trade_id',
        'symbol',
        'user',
        'clearing_house',
        'settlement_type',
        'status',
        'settlement_date',
    )
    list_filter = ('status', 'settlement_type', 'clearing_house', 'settlement_date')
    search_fields = ('trade_id', 'symbol', 'user__username')
    date_hierarchy = 'settlement_date'


@admin.register(MarginRequirement)
class MarginRequirementAdmin(admin.ModelAdmin):
    list_display = (
        'clearing_account',
        'initial_margin',
        'maintenance_margin',
        'collateral_posted',
        'margin_call_amount',
        'is_margin_call_active',
    )
    list_filter = ('is_margin_call_active',)
    search_fields = ('clearing_account__account_number', 'clearing_account__account_name')


@admin.register(SettlementReconciliation)
class SettlementReconciliationAdmin(admin.ModelAdmin):
    list_display = ('id', 'settlement', 'break_type', 'status', 'resolved_by', 'created_at')
    list_filter = ('break_type', 'status', 'created_at')
    search_fields = ('settlement__trade_id', 'description')
    
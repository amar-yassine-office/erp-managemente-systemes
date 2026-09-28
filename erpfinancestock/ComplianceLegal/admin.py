from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    AuditLog,
    ComplianceCheck,
    RestrictedAsset,
    SuspiciousActivityReport,
    TradeSurveillanceRule,
)


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ('user', 'check_type', 'status', 'performed_by', 'checked_at', 'next_review_date')
    list_filter = ('check_type', 'status', 'checked_at')
    search_fields = ('user__username', 'user__email', 'notes')


@admin.register(RestrictedAsset)
class RestrictedAssetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'reason', 'is_active', 'start_date', 'end_date', 'added_by')
    list_filter = ('reason', 'is_active', 'start_date')
    search_fields = ('symbol', 'company_name')


@admin.register(SuspiciousActivityReport)
class SuspiciousActivityReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'user',
        'portfolio_account_number',
        'severity',
        'status',
        'investigated_by',
        'created_at',
    )
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('user__username', 'title', 'description', 'portfolio_account_number')


@admin.register(TradeSurveillanceRule)
class TradeSurveillanceRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'rule_type', 'threshold_value', 'is_active', 'created_at')
    list_filter = ('rule_type', 'is_active')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action_type', 'target_model', 'target_id', 'ip_address')
    list_filter = ('action_type', 'target_model', 'timestamp')
    search_fields = ('actor__username', 'target_model', 'target_id', 'ip_address')
    readonly_fields = ('actor', 'action_type', 'target_model', 'target_id', 'ip_address', 'changes', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import APIKey, AsyncTaskLog, SystemIncident, SystemServer, SystemSetting


class SystemIncidentInline(admin.TabularInline):
    model = SystemIncident
    extra = 0
    fields = ('title', 'severity', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(SystemServer)
class SystemServerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'ip_address',
        'server_type',
        'status',
        'cpu_usage_pct',
        'memory_usage_pct',
        'last_ping',
    )
    list_filter = ('server_type', 'status')
    search_fields = ('name', 'ip_address')
    inlines = [SystemIncidentInline]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key_name', 'user', 'is_active', 'rate_limit_per_minute', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('key_name', 'user__username', 'api_key')


@admin.register(AsyncTaskLog)
class AsyncTaskLogAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'task_id', 'status', 'runtime_seconds', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('task_name', 'task_id')
    readonly_fields = ('created_at',)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_encrypted', 'updated_at')
    search_fields = ('key', 'description')


@admin.register(SystemIncident)
class SystemIncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'server', 'severity', 'status', 'reported_by', 'created_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('title', 'description', 'server__name')
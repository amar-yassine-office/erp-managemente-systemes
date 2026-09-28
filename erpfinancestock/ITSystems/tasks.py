from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from .models import (
    SystemServer,
    APIKey,
    AsyncTaskLog,
    SystemSetting,
    SystemIncident,
)
from .cache import ITSystemsCacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def monitor_server_health_task(self, server_id: int, cpu_pct: float, memory_pct: float):
    """
    مهمة غير متزامنة لتحديث حالة السيرفر (Health Check)، وفحص العتبات المرتفعة
    لاستخدام الموارد (CPU/RAM) وإنشاء بلاغ حادثة (SystemIncident) تلقائياً عند الخطر.
    """
    try:
        server = SystemServer.objects.get(id=server_id)
        cpu = Decimal(str(cpu_pct))
        memory = Decimal(str(memory_pct))

        server.cpu_usage_pct = cpu
        server.memory_usage_pct = memory

        # تحديث حالة السيرفر بناءً على استخدام الموارد
        if cpu > Decimal('90.00') or memory > Decimal('90.00'):
            server.status = 'DEGRADED'
            # إنشاء حادثة تلقائية في حالة الإجهاد العالي
            SystemIncident.objects.create(
                server=server,
                title=f"High Resource Usage Alert on {server.name}",
                description=f"CPU usage reached {cpu}% and Memory usage reached {memory}%.",
                severity='HIGH',
                status='OPEN'
            )
        elif server.status == 'DEGRADED' and cpu <= Decimal('75.00') and memory <= Decimal('75.00'):
            server.status = 'ONLINE'

        server.save(update_fields=['cpu_usage_pct', 'memory_usage_pct', 'status', 'last_ping'])

        # إبطال الكاش الخاص بالخوادم
        ITSystemsCacheService.invalidate_server_cache(server_id)

        return f"Health check logged for server {server.name} ({server.status})"

    except SystemServer.DoesNotExist:
        logger.error(f"SystemServer ID {server_id} not found.")
        return None
    except Exception as exc:
        logger.error(f"Error monitoring server health for ID {server_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def purge_old_async_task_logs_task(days_to_keep: int = 30):
    """
    مهمة تنظيف دورية لإزالة سجلات المهام الخلفية (AsyncTaskLog) القديمة
    للحفاظ على أداء وسرعة قاعدة البيانات.
    """
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    deleted_count, _ = AsyncTaskLog.objects.filter(created_at__lt=cutoff_date).delete()

    logger.info(f"Purged {deleted_count} async task logs older than {days_to_keep} days.")
    return f"Purged {deleted_count} stale task log records."


@shared_task
def revoke_expired_api_keys_task():
    """
    مهمة فحص وتعطيل مفاتيح الـ API المنتهية الصلاحية تلقائياً.
    """
    now = timezone.now()
    expired_keys = APIKey.objects.filter(is_active=True, expires_at__lt=now)
    updated_count = expired_keys.update(is_active=False)

    if updated_count > 0:
        ITSystemsCacheService.invalidate_api_keys_cache()

    return f"Revoked {updated_count} expired API keys."


@shared_task
def sync_global_system_setting_task(setting_key: str, new_value: str):
    """
    مهمة غير متزامنة لتحديث وتطبيق إعدادات النظام العامة عبر السيرفرات وإبطال الكاش الخاص بها.
    """
    try:
        setting, _ = SystemSetting.objects.update_or_create(
            key=setting_key,
            defaults={'value': new_value}
        )
        ITSystemsCacheService.invalidate_system_setting_cache(setting_key)
        return f"System setting '{setting_key}' updated successfully."
    except Exception as exc:
        logger.error(f"Failed to sync setting {setting_key}: {exc}")
        return None
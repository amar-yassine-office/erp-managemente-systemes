from django.core.cache import cache
from .models import SystemServer, APIKey, AsyncTaskLog, SystemSetting, SystemIncident


class ITSystemsCacheService:
    """
    خدمة التخزين المؤقت المخصصة لتطبيق ITSystems.
    تتعامل مع Redis مباشرة لجلب البيانات وإبطالها بدون الحاجة لـ Signals.
    """

    # =========================================================================
    # 1. APIKey Caching
    # =========================================================================
    @staticmethod
    def get_active_api_key(raw_api_key: str):
        """
        جلب مفتاح الـ API المعتمد من الـ Cache بدلاً من الاستعلام المتكرر من DB.
        """
        cache_key = f"itsystems:apikey:{raw_api_key}"
        api_key_obj = cache.get(cache_key)

        if api_key_obj is None:
            try:
                api_key_obj = APIKey.objects.select_related('user').get(
                    api_key=raw_api_key,
                    is_active=True
                )
                cache.set(cache_key, api_key_obj, timeout=86400)  # تخزين لمدة 24 ساعة
            except APIKey.DoesNotExist:
                return None

        return api_key_obj

    @staticmethod
    def invalidate_api_key(raw_api_key: str):
        """مسح كاش مفتاح الـ API المخصص."""
        cache_key = f"itsystems:apikey:{raw_api_key}"
        cache.delete(cache_key)

    # =========================================================================
    # 2. SystemSetting Caching
    # =========================================================================
    @staticmethod
    def get_setting(key_name: str, default=None):
        """
        جلب قيمة إعداد معين من النظام مباشرة من الـ Cache.
        """
        cache_key = f"itsystems:setting:{key_name}"
        value = cache.get(cache_key)

        if value is None:
            try:
                setting_obj = SystemSetting.objects.get(key=key_name)
                value = setting_obj.value
                cache.set(cache_key, value, timeout=86400)  # تخزين لمدة 24 ساعة
            except SystemSetting.DoesNotExist:
                return default

        return value

    @staticmethod
    def invalidate_setting(key_name: str):
        """مسح إعداد معين من الـ Cache عند التعديل."""
        cache_key = f"itsystems:setting:{key_name}"
        cache.delete(cache_key)

    # =========================================================================
    # 3. SystemServer Caching
    # =========================================================================
    @staticmethod
    def get_server_health_summary():
        """
        تخزين وحساب ملخص حالة البنية التحتية والسيرفرات لمدة دقيقة للوحة التحكم.
        """
        cache_key = "itsystems:servers:health_summary"
        summary = cache.get(cache_key)

        if summary is None:
            qs = SystemServer.objects.all()
            summary = {
                'total_servers': qs.count(),
                'online_count': qs.filter(status='ONLINE').count(),
                'degraded_count': qs.filter(status='DEGRADED').count(),
                'critical_count': qs.filter(status='OFFLINE').count(),
            }
            cache.set(cache_key, summary, timeout=60)  # تخزين لمدة دقيقة واحدة

        return summary

    @staticmethod
    def invalidate_server_health_summary():
        """مسح ملخص حالة السيرفرات."""
        cache.delete("itsystems:servers:health_summary")

    # =========================================================================
    # 4. SystemIncident Caching
    # =========================================================================
    @staticmethod
    def get_open_incidents():
        """
        تخزين قائمة الأعطال والمشاكل المفتوحة والنشطة حالياً لمدة 15 دقيقة.
        """
        cache_key = "itsystems:incidents:open_list"
        open_incidents = cache.get(cache_key)

        if open_incidents is None:
            open_incidents = list(
                SystemIncident.objects.filter(status__in=['OPEN', 'INVESTIGATING', 'IDENTIFIED'])
                .select_related('server', 'reported_by')
            )
            cache.set(cache_key, open_incidents, timeout=900)  # تخزين لمدة 15 دقيقة

        return open_incidents

    @staticmethod
    def invalidate_incidents_cache():
        """مسح كاش الحوادث النشطة وملخص حالة السيرفرات."""
        cache.delete("itsystems:incidents:open_list")
        cache.delete("itsystems:servers:health_summary")

    # =========================================================================
    # 5. AsyncTaskLog Caching
    # =========================================================================
    @staticmethod
    def get_task_failure_rate():
        """
        حساب نسبة فشل المهام للخلفية (Celery) وتخزينها لمدة 5 دقائق.
        """
        cache_key = "itsystems:tasks:failure_rate"
        rate = cache.get(cache_key)

        if rate is None:
            total_tasks = AsyncTaskLog.objects.count()
            if total_tasks > 0:
                failed_tasks = AsyncTaskLog.objects.filter(status='FAILURE').count()
                rate = (failed_tasks / total_tasks) * 100
            else:
                rate = 0.00
            rate = round(rate, 2)
            cache.set(cache_key, rate, timeout=300)  # تخزين لمدة 5 دقائق

        return rate
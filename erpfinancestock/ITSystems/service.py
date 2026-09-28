from typing import Dict, Any

# استيراد المهام المباشر من tasks.py
from .tasks import (
    monitor_server_health_task,
    purge_old_async_task_logs_task,
    revoke_expired_api_keys_task,
    sync_global_system_setting_task,
)
from .cache import ITSystemsCacheService


class ITSystemsService:
    """
    طبقة الخدمات (Service Layer) الخاصة بقسم أنظمة البنية التحتية والدعم الفني.
    تتعامل مع الاستدعاءات غير المتزامنة وربطها بصف الكاش.
    """

    @staticmethod
    def record_server_metrics(server_id: int, cpu_usage: float, memory_usage: float):
        """
        جدولة مهمة تسليم قياسات السيرفر وفحص الحالة في الخلفية.
        """
        task = monitor_server_health_task.delay(
            server_id=server_id,
            cpu_pct=cpu_usage,
            memory_pct=memory_usage
        )
        return {"status": "metrics_queued", "task_id": task.id}

    @staticmethod
    def cleanup_stale_task_logs(days_retention: int = 30):
        """
        جدولة مهمة تنظيف السجلات القديمة.
        """
        task = purge_old_async_task_logs_task.delay(days_to_keep=days_retention)
        return {"status": "cleanup_queued", "task_id": task.id}

    @staticmethod
    def deactivate_expired_keys():
        """
        جدولة مهمة تعطيل مفاتيح الـ API المنتهية.
        """
        task = revoke_expired_api_keys_task.delay()
        return {"status": "key_revocation_queued", "task_id": task.id}

    @staticmethod
    def update_system_setting(key: str, value: str):
        """
        تحديث إعدادات النظام عبر مهمة غير متزامنة.
        """
        task = sync_global_system_setting_task.delay(setting_key=key, new_value=value)
        return {"status": "setting_update_queued", "task_id": task.id}

    @staticmethod
    def get_infrastructure_health_dashboard():
        """
        استرجاع حالة البنية التحتية، السيرفرات، والحوادث المفتوحة فوراً من Caching.
        """
        servers = ITSystemsCacheService.get_all_servers_cache()
        open_incidents = ITSystemsCacheService.get_open_incidents_cache()
        system_status = ITSystemsCacheService.get_overall_system_status_cache()

        return {
            "overall_status": system_status,
            "servers": servers,
            "active_incidents": open_incidents,
        }
    #those the operation logic on the models 

    import secrets
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    SystemServer,
    APIKey,
    AsyncTaskLog,
    SystemSetting,
    SystemIncident,
)
from .schemas import (
    SystemServerCreateSchema,
    SystemServerUpdateSchema,
    APIKeyCreateSchema,
    APIKeyUpdateSchema,
    AsyncTaskLogCreateSchema,
    AsyncTaskLogUpdateSchema,
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
    SystemIncidentCreateSchema,
    SystemIncidentUpdateSchema,
)

User = get_user_model()


class ITSystemsService:

    # =====================================================================
    # 1. SYSTEM SERVER SERVICES
    # =====================================================================

    @classmethod
    @transaction.atomic
    def create_server(cls, staff_user: User, data: SystemServerCreateSchema) -> SystemServer:
        server = SystemServer.objects.create(
            name=data.name,
            ip_address=data.ip_address,
            server_type=data.server_type,
            status=data.status,
            cpu_usage_pct=data.cpu_usage_pct,
            memory_usage_pct=data.memory_usage_pct,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="SystemServer", target_id=str(server.id))
        return server

    @classmethod
    @transaction.atomic
    def update_server(cls, server_id: int, staff_user: User, data: SystemServerUpdateSchema) -> SystemServer:
        server = get_object_or_404(SystemServer, id=server_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(server, key, value)
        server.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="SystemServer", target_id=str(server.id), changes=update_data)
        return server

    @staticmethod
    def list_servers(server_type: Optional[str] = None, status: Optional[str] = None) -> List[SystemServer]:
        qs = SystemServer.objects.all()
        if server_type:
            qs = qs.filter(server_type=server_type)
        if status:
            qs = qs.filter(status=status)
        return qs

    # =====================================================================
    # 2. API KEY SERVICES
    # =====================================================================

    @classmethod
    @transaction.atomic
    def generate_api_key(cls, staff_user: User, data: APIKeyCreateSchema) -> APIKey:
        target_user = get_object_or_404(User, id=data.user_id)
        # Generate a secure 128-character unique hex key
        raw_api_key = secrets.token_hex(64)
        
        api_key_obj = APIKey.objects.create(
            user=target_user,
            key_name=data.key_name,
            api_key=raw_api_key,
            rate_limit_per_minute=data.rate_limit_per_minute,
            expires_at=data.expires_at,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="APIKey", target_id=str(api_key_obj.id))
        return api_key_obj

    @classmethod
    @transaction.atomic
    def update_api_key(cls, key_id: int, staff_user: User, data: APIKeyUpdateSchema) -> APIKey:
        api_key_obj = get_object_or_404(APIKey, id=key_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(api_key_obj, key, value)
        api_key_obj.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="APIKey", target_id=str(api_key_obj.id), changes=update_data)
        return api_key_obj

    @staticmethod
    def list_api_keys(user_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[APIKey]:
        qs = APIKey.objects.select_related("user").all()
        if user_id:
            qs = qs.filter(user_id=user_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    # =====================================================================
    # 3. ASYNC TASK LOG SERVICES
    # =====================================================================

    @classmethod
    @transaction.atomic
    def create_task_log(cls, data: AsyncTaskLogCreateSchema) -> AsyncTaskLog:
        task_log = AsyncTaskLog.objects.create(
            task_id=data.task_id,
            task_name=data.task_name,
            status=data.status,
            runtime_seconds=data.runtime_seconds,
            traceback=data.traceback or "",
            completed_at=data.completed_at,
        )
        return task_log

    @classmethod
    @transaction.atomic
    def update_task_log(cls, task_id_str: str, data: AsyncTaskLogUpdateSchema) -> AsyncTaskLog:
        task_log = get_object_or_404(AsyncTaskLog, task_id=task_id_str)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task_log, key, value)
        task_log.save()
        return task_log

    @staticmethod
    def list_task_logs(status: Optional[str] = None, task_name: Optional[str] = None) -> List[AsyncTaskLog]:
        qs = AsyncTaskLog.objects.all()
        if status:
            qs = qs.filter(status=status)
        if task_name:
            qs = qs.filter(task_name__icontains=task_name)
        return qs

    # =====================================================================
    # 4. SYSTEM SETTING SERVICES
    # =====================================================================

    @classmethod
    @transaction.atomic
    def set_system_setting(cls, staff_user: User, data: SystemSettingCreateSchema) -> SystemSetting:
        setting, created = SystemSetting.objects.update_or_create(
            key=data.key,
            defaults={
                "value": data.value,
                "description": data.description or "",
                "is_encrypted": data.is_encrypted,
            },
        )
        action = "CREATE" if created else "UPDATE"
        cls.log_audit_event(actor=staff_user, action_type=action, target_model="SystemSetting", target_id=str(setting.id), changes={"key": data.key})
        return setting

    @staticmethod
    def get_system_setting(key: str) -> Optional[SystemSetting]:
        return SystemSetting.objects.filter(key=key).first()

    @staticmethod
    def list_system_settings() -> List[SystemSetting]:
        return SystemSetting.objects.all()

    # =====================================================================
    # 5. SYSTEM INCIDENT SERVICES
    # =====================================================================

    @classmethod
    @transaction.atomic
    def create_incident(cls, staff_user: User, data: SystemIncidentCreateSchema) -> SystemIncident:
        server = get_object_or_404(SystemServer, id=data.server_id) if data.server_id else None
        incident = SystemIncident.objects.create(
            server=server,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=data.status,
            reported_by=staff_user,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="SystemIncident", target_id=str(incident.id))
        return incident

    @classmethod
    @transaction.atomic
    def update_incident(cls, incident_id: int, staff_user: User, data: SystemIncidentUpdateSchema) -> SystemIncident:
        incident = get_object_or_404(SystemIncident, id=incident_id)
        update_data = data.dict(exclude_unset=True)
        
        # If status is changing to RESOLVED and resolved_at isn't provided, timestamp it automatically
        if update_data.get("status") == "RESOLVED" and not update_data.get("resolved_at"):
            update_data["resolved_at"] = timezone.now()

        for key, value in update_data.items():
            setattr(incident, key, value)
        incident.save()
        
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="SystemIncident", target_id=str(incident.id), changes=update_data)
        return incident

    @staticmethod
    def list_incidents(severity: Optional[str] = None, status: Optional[str] = None) -> List[SystemIncident]:
        qs = SystemIncident.objects.select_related("server", "reported_by").all()
        if severity:
            qs = qs.filter(severity=severity)
        if status:
            qs = qs.filter(status=status)
        return qs

    # =====================================================================
    # AUDIT LOG HELPER (Shared structure consistency)
    # =====================================================================

    @staticmethod
    def log_audit_event(actor: Optional[User], action_type: str, target_model: str, target_id: str = "", changes: Optional[Dict[str, Any]] = None):
        # Imports AuditLog dynamically or references ComplianceLegal's or a shared one if unified.
        # Assuming we register standard logging or cross-reference safely:
        from ComplianceLegal.models import AuditLog
        AuditLog.objects.create(
            actor=actor if actor and actor.is_authenticated else None,
            action_type=action_type,
            target_model=target_model,
            target_id=target_id,
            changes=changes or {},
        )
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from .models import ClientProfile, LeadPipeline

TTL_12_HOURS = 43200
TTL_1_HOUR = 3600


class ClientRelationsCache:

    @staticmethod
    def get_client_profile_summary(client_id: int) -> Optional[Dict[str, Any]]:
        """كاش للملف الشخصي الأساسي للعميل بدلاً من الاستعلام المتكرر."""
        key = f"client_relations:profile:{client_id}"
        data = cache.get(key)

        if data is None:
            try:
                profile = ClientProfile.objects.select_related('user', 'relationship_manager').get(id=client_id)
                data = {
                    "id": profile.id,
                    "full_name": profile.user.get_full_name() or profile.user.username,
                    "client_type": profile.client_type,
                    "risk_tolerance": profile.risk_tolerance,
                    "net_worth_estimate": float(profile.net_worth_estimate) if profile.net_worth_estimate else 0.0,
                    "manager_name": profile.relationship_manager.get_full_name() if profile.relationship_manager else "Unassigned",
                }
                cache.set(key, data, TTL_12_HOURS)
            except ClientProfile.DoesNotExist:
                return None

        return data

    @staticmethod
    def get_lead_pipeline_stats() -> Dict[str, Any]:
        """كاش لإحصائيات مسار المبيعات (Pipeline Metrics) لمدة ساعة."""
        key = "client_relations:leads:stats"
        data = cache.get(key)

        if data is None:
            stages = LeadPipeline.STAGE_CHOICES
            stats = {}
            for code, name in stages:
                stats[code] = LeadPipeline.objects.filter(stage=code).count()

            data = {
                "total_leads": LeadPipeline.objects.count(),
                "by_stage": stats
            }
            cache.set(key, data, TTL_1_HOUR)

        return data
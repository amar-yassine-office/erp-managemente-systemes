from typing import List, Set, Dict, Any
from django.core.cache import cache
from .models import RestrictedAsset, TradeSurveillanceRule

TTL_24_HOURS = 86400
TTL_1_HOUR = 3600


class ComplianceLegalCache:

    @staticmethod
    def get_restricted_symbols_set() -> Set[str]:
        """
        تخزين قائمة الرموز المقيدة (Restricted Symbols) في Redis على شكل Set.
        يتم استدعاء هذه الخدمة في محرك التداول لمنع تنفيذ أي أمر على أصل محظور بسرعة O(1).
        """
        key = "compliance:restricted_assets:symbols"
        symbols = cache.get(key)

        if symbols is None:
            symbols = set(
                RestrictedAsset.objects.filter(is_active=True).values_list('symbol', flat=True)
            )
            cache.set(key, symbols, TTL_24_HOURS)

        return symbols

    @staticmethod
    def is_symbol_restricted(symbol: str) -> bool:
        """فحص سريع لمعرفة هل رمز السهم/الأصل محظور حالياً."""
        restricted_set = ComplianceLegalCache.get_restricted_symbols_set()
        return symbol.upper() in restricted_set

    @staticmethod
    def get_active_surveillance_rules() -> List[Dict[str, Any]]:
        """
        تخزين قواعد المراقبة النشطة مؤقتاً لتقليل استعلامات قاعدة البيانات عند الفحص التلقائي.
        """
        key = "compliance:surveillance_rules:active"
        rules = cache.get(key)

        if rules is None:
            active_queryset = TradeSurveillanceRule.objects.filter(is_active=True)
            rules = [
                {
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "threshold_value": float(rule.threshold_value),
                }
                for rule in active_queryset
            ]
            cache.set(key, rules, TTL_1_HOUR)

        return rules

    @staticmethod
    def invalidate_restricted_assets_cache():
        """إبطال كاش الأصول المحظورة عند إضافة أو تعديل أصل مقيد من قبل فريق الامتثال."""
        cache.delete("compliance:restricted_assets:symbols")

    @staticmethod
    def invalidate_surveillance_rules_cache():
        """إبطال كاش قواعد المراقبة عند تحديثها."""
        cache.delete("compliance:surveillance_rules:active")
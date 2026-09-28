from django.core.cache import cache
from django.db.models import Sum, Count, F
from .models import (
    ClearingHouse,
    ClearingMemberAccount,
    TradeSettlement,
    MarginRequirement,
    SettlementReconciliation,
)


class OperationsClearingCacheService:
    """
    خدمة التخزين المؤقت المخصصة لتطبيق OperationsClearing.
    تتعامل مع Redis لقراءة وتخزين بيانات المقاصة والتسويات والأرصدة وإبطالها عند الحاجة.
    """

    # =========================================================================
    # 1. ClearingHouse Caching (بيانات مرجعية شبه ثابته)
    # =========================================================================
    @staticmethod
    def get_active_clearing_houses():
        """
        تخزين قائمة بيوت المقاصة النشطة (مثل DTCC, Euroclear).
        بيانات شبه ثابته تقرأ بكثرة، تخزن لمدة 24 ساعة.
        """
        cache_key = "clearing:houses:active_list"
        clearing_houses = cache.get(cache_key)

        if clearing_houses is None:
            clearing_houses = list(
                ClearingHouse.objects.filter(is_active=True).values('id', 'name', 'code', 'country')
            )
            cache.set(cache_key, clearing_houses, timeout=86400)  # 24 ساعة

        return clearing_houses

    @staticmethod
    def invalidate_clearing_houses_cache():
        """مسح كاش بيوت المقاصة النشطة عند إضافة أو تعديل بيت مقاصة."""
        cache.delete("clearing:houses:active_list")

    # =========================================================================
    # 2. ClearingMemberAccount Caching (أرصدة حسابات المقاصة)
    # =========================================================================
    @staticmethod
    def get_account_balance(account_id: int):
        """
        جلب وتخزين رصيد حساب المقاصة المباشر لمدة 5 دقائق.
        """
        cache_key = f"clearing:account:{account_id}:balance"
        account_data = cache.get(cache_key)

        if account_data is None:
            try:
                acc = ClearingMemberAccount.objects.select_related('clearing_house').get(id=account_id)
                account_data = {
                    'account_id': acc.id,
                    'account_number': acc.account_number,
                    'account_name': acc.account_name,
                    'clearing_house_code': acc.clearing_house.code,
                    'balance': float(acc.balance),
                    'currency': acc.currency,
                    'is_active': acc.is_active,
                }
                cache.set(cache_key, account_data, timeout=300)  # 5 دقائق
            except ClearingMemberAccount.DoesNotExist:
                return None

        return account_data

    @staticmethod
    def invalidate_account_cache(account_id: int):
        """مسح كاش حساب المقاصة المخصص عند تغيير الرصيد أو الحالة."""
        cache.delete(f"clearing:account:{account_id}:balance")

    # =========================================================================
    # 3. TradeSettlement Caching (تسويات الصفقات والإحصائيات)
    # =========================================================================
    @staticmethod
    def get_pending_settlements_summary():
        """
        تخزين وحساب ملخص التسويات المعلقة (Pending Volume & Value) لمدة دقيقة واحدة.
        مفيد للوحة التحكم (Dashboard) للعمليات المالية.
        """
        cache_key = "clearing:settlements:pending_summary"
        summary = cache.get(cache_key)

        if summary is None:
            pending_qs = TradeSettlement.objects.filter(status='PENDING')
            summary = {
                'pending_count': pending_qs.count(),
                'total_pending_amount': float(
                    pending_qs.aggregate(total=Sum('total_amount'))['total'] or 0.00
                ),
            }
            cache.set(cache_key, summary, timeout=60)  # 1 minute

        return summary

    @staticmethod
    def get_user_settlement_history(user_id: int):
        """
        تخزين قائمة آخر التسويات الخاصة بالمستخدم لمدة 10 دقائق.
        """
        cache_key = f"clearing:user:{user_id}:settlements"
        settlements = cache.get(cache_key)

        if settlements is None:
            settlements = list(
                TradeSettlement.objects.filter(user_id=user_id)
                .select_related('clearing_house', 'clearing_account')
                .values(
                    'trade_id', 'symbol', 'quantity', 'price', 
                    'total_amount', 'settlement_type', 'status', 'settlement_date'
                )[:50]  # جلب آخر 50 تسوية
            )
            cache.set(cache_key, settlements, timeout=600)  # 10 دقائق

        return settlements

    @staticmethod
    def invalidate_settlement_cache(user_id: int = None):
        """مسح كاش التسويات المعلقة وكاش المستخدم فور إتمام/تعديل تسوية."""
        cache.delete("clearing:settlements:pending_summary")
        if user_id:
            cache.delete(f"clearing:user:{user_id}:settlements")

    # =========================================================================
    # 4. MarginRequirement Caching (متطلبات الهامش و Margin Calls)
    # =========================================================================
    @staticmethod
    def get_account_margin_status(clearing_account_id: int):
        """
        تخزين متطلبات الهامش والـ Margin Calls للحساب لمدة 3 دقائق.
        """
        cache_key = f"clearing:margin:account:{clearing_account_id}"
        margin_data = cache.get(cache_key)

        if margin_data is None:
            try:
                margin = MarginRequirement.objects.get(clearing_account_id=clearing_account_id)
                margin_data = {
                    'account_id': clearing_account_id,
                    'initial_margin': float(margin.initial_margin),
                    'maintenance_margin': float(margin.maintenance_margin),
                    'collateral_posted': float(margin.collateral_posted),
                    'margin_call_amount': float(margin.margin_call_amount),
                    'is_margin_call_active': margin.is_margin_call_active,
                    'last_updated': margin.last_updated.isoformat() if margin.last_updated else None,
                }
                cache.set(cache_key, margin_data, timeout=180)  # 3 دقائق
            except MarginRequirement.DoesNotExist:
                return None

        return margin_data

    @staticmethod
    def get_active_margin_calls():
        """
        تخزين جميع الحسابات المطلوبة للـ Margin Call النشطة لمراقبة المخاطر (Risk Monitor).
        """
        cache_key = "clearing:margin:active_calls_list"
        active_calls = cache.get(cache_key)

        if active_calls is None:
            active_calls = list(
                MarginRequirement.objects.filter(is_margin_call_active=True)
                .select_related('clearing_account')
                .values('clearing_account__account_number', 'margin_call_amount', 'collateral_posted')
            )
            cache.set(cache_key, active_calls, timeout=300)  # 5 دقائق

        return active_calls

    @staticmethod
    def invalidate_margin_cache(clearing_account_id: int):
        """مسح كاش الهامش والـ Margin Calls عند ضخ سيولة أو تغير المتطلبات."""
        cache.delete(f"clearing:margin:account:{clearing_account_id}")
        cache.delete("clearing:margin:active_calls_list")

    # =========================================================================
    # 5. SettlementReconciliation Caching (مطابقة وتسوية الفروقات)
    # =========================================================================
    @staticmethod
    def get_open_reconciliation_breaks():
        """
        تخزين قائمة الفروقات والمشاكل المعلقة (Open Discrepancies) لمسؤولي المقاصة.
        تخزن لمدة 15 دقيقة.
        """
        cache_key = "clearing:reconciliations:open_breaks"
        open_breaks = cache.get(cache_key)

        if open_breaks is None:
            open_breaks = list(
                SettlementReconciliation.objects.filter(status__in=['OPEN', 'INVESTIGATING'])
                .select_related('settlement')
                .values(
                    'id', 'settlement__trade_id', 'break_type', 
                    'description', 'status', 'created_at'
                )
            )
            cache.set(cache_key, open_breaks, timeout=900)  # 15 دقيقة

        return open_breaks

    @staticmethod
    def invalidate_reconciliation_cache():
        """مسح كاش الفروقات المفتوحة عند حل أو تسجيل مشكلة تسوية جديدة."""
        cache.delete("clearing:reconciliations:open_breaks")
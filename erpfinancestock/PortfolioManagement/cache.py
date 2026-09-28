from decimal import Decimal
from django.core.cache import cache
from .models import AssetAllocation, Portfolio, PortfolioPosition, PortfolioPerformance


class PortfolioManagementCacheService:
    """
    خدمة التخزين المؤقت المخصصة لتطبيق PortfolioManagement.
    تتعامل مع Redis لقراءة وتخزين بيانات المحافظ، مراكز الأسهم، والإحصائيات وإبطالها عند التعديل.
    """

    # =========================================================================
    # 1. AssetAllocation Caching (استراتيجيات توزيع الأصول)
    # =========================================================================
    @staticmethod
    def get_all_asset_allocations():
        """
        تخزين قائمة جميع استراتيجيات توزيع الأصول (Aggressive, Balanced...).
        بيانات مرجعية شبه ثابته تقرأ بكثرة، تخزن لمدة 24 ساعة.
        """
        cache_key = "portfolio:asset_allocations:list"
        strategies = cache.get(cache_key)

        if strategies is None:
            strategies = list(
                AssetAllocation.objects.values(
                    'id', 'name', 'target_stocks_pct', 'target_bonds_pct', 'target_cash_pct'
                )
            )
            cache.set(cache_key, strategies, timeout=86400)  # 24 ساعة

        return strategies

    @staticmethod
    def invalidate_asset_allocations():
        """مسح كاش الاستراتيجيات عند إضافة أو تعديل استراتيجية."""
        cache.delete("portfolio:asset_allocations:list")

    # =========================================================================
    # 2. Portfolio Caching (بيانات المحفظة والقيمة الكلية)
    # =========================================================================
    @staticmethod
    def get_portfolio_summary(portfolio_id: int):
        """
        تخزين تفاصيل المحفظة ورصيدها النقدي وقيمتها الكلية لمدة 5 دقائق.
        """
        cache_key = f"portfolio:detail:{portfolio_id}"
        portfolio_data = cache.get(cache_key)

        if portfolio_data is None:
            try:
                p = Portfolio.objects.select_related('strategy', 'user').get(id=portfolio_id)
                portfolio_data = {
                    'id': p.id,
                    'user_id': p.user_id,
                    'account_number': p.account_number,
                    'name': p.name,
                    'status': p.status,
                    'strategy_name': p.strategy.name if p.strategy else None,
                    'cash_balance': float(p.cash_balance),
                    'total_value': float(p.total_value),
                }
                cache.set(cache_key, portfolio_data, timeout=300)  # 5 دقائق
            except Portfolio.DoesNotExist:
                return None

        return portfolio_data

    @staticmethod
    def get_user_portfolios(user_id: int):
        """
        تخزين قائمة المحافظ النشطة الخاصة بمستخدم معين لمدة 10 دقائق.
        """
        cache_key = f"portfolio:user:{user_id}:list"
        portfolios = cache.get(cache_key)

        if portfolios is None:
            portfolios = list(
                Portfolio.objects.filter(user_id=user_id, status='ACTIVE')
                .values('id', 'account_number', 'name', 'cash_balance', 'total_value')
            )
            cache.set(cache_key, portfolios, timeout=600)  # 10 دقائق

        return portfolios

    @staticmethod
    def invalidate_portfolio_cache(portfolio_id: int, user_id: int = None):
        """مسح كاش التفاصيل وكاش مستخدم المحفظة عند تغير القيم أو الحالة."""
        cache.delete(f"portfolio:detail:{portfolio_id}")
        if user_id:
            cache.delete(f"portfolio:user:{user_id}:list")

    # =========================================================================
    # 3. PortfolioPosition Caching (مراكز الأسهم والأصول داخل المحفظة)
    # =========================================================================
    @staticmethod
    def get_portfolio_positions(portfolio_id: int):
        """
        تخزين قائمة مراكز الأسهم داخل المحفظة (الكمية، سعر الشراء، السعر الحالي) لمدة 3 دقائق.
        """
        cache_key = f"portfolio:{portfolio_id}:positions"
        positions = cache.get(cache_key)

        if positions is None:
            positions = list(
                PortfolioPosition.objects.filter(portfolio_id=portfolio_id)
                .values('id', 'symbol', 'quantity', 'average_buy_price', 'current_price', 'updated_at')
            )
            # تحويل القيم لأسلوب Float لسهولة الـ JSON Serialization في الـ APIs
            for pos in positions:
                pos['quantity'] = float(pos['quantity'])
                pos['average_buy_price'] = float(pos['average_buy_price'])
                pos['current_price'] = float(pos['current_price'])
                pos['market_value'] = pos['quantity'] * pos['current_price']

            cache.set(cache_key, positions, timeout=180)  # 3 دقائق

        return positions

    @staticmethod
    def invalidate_positions_cache(portfolio_id: int):
        """مسح كاش مراكز الأسهم وكاش المحفظة المرتبط عند الشراء/البيع أو تحديث الأسعار."""
        cache.delete(f"portfolio:{portfolio_id}:positions")
        cache.delete(f"portfolio:detail:{portfolio_id}")

    # =========================================================================
    # 4. PortfolioPerformance Caching (السجل التاريخي للـ NAV والأداء)
    # =========================================================================
    @staticmethod
    def get_portfolio_performance_history(portfolio_id: int, limit: int = 30):
        """
        تخزين السجل التاريخي لقيمة أصول المحفظة (NAV) وأدائها اليومي (آخر 30 يوم) لمدة ساعة.
        تستخدم لرسم المخططات البيانية (Charts).
        """
        cache_key = f"portfolio:{portfolio_id}:performance:limit_{limit}"
        history = cache.get(cache_key)

        if history is None:
            history = list(
                PortfolioPerformance.objects.filter(portfolio_id=portfolio_id)
                .values('date', 'nav_value', 'daily_return_pct')[:limit]
            )
            for item in history:
                item['date'] = item['date'].isoformat()
                item['nav_value'] = float(item['nav_value'])
                item['daily_return_pct'] = float(item['daily_return_pct'])

            cache.set(cache_key, history, timeout=3600)  # ساعة واحدة

        return history

    @staticmethod
    def invalidate_performance_cache(portfolio_id: int):
        """مسح كاش السجل التاريخي فور إضافة أداء يوم جديد."""
        # مسح الأحجام الشائعة
        cache.delete(f"portfolio:{portfolio_id}:performance:limit_30")
        cache.delete(f"portfolio:{portfolio_id}:performance:limit_90")
        cache.delete(f"portfolio:{portfolio_id}:performance:limit_365")
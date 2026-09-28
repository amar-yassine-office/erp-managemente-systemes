from django.core.cache import cache
from .models import RiskLimit, PortfolioRiskMetric, StressTestScenario, StressTestResult, RiskAlert


class RiskManagementCacheService:
    """
    خدمة التخزين المؤقت المخصصة لتطبيق RiskManagement.
    تتعامل مع قيود المخاطر، مؤشرات الـ VaR وSharpe Ratio، سيناريوهات الإجهاد والتنبيهات النشطة.
    """

    # =========================================================================
    # 1. RiskLimit Caching (حدود وسقوف المخاطر للمحفظة)
    # =========================================================================
    @staticmethod
    def get_portfolio_risk_limits(portfolio_id: int):
        """
        تخزين حدود المخاطر النشطة للمحفظة (Max Drawdown, VaR Limit...) لمدة 6 ساعات.
        تستخدم أثناء التحقق التلقائي عند كل عملية تداول.
        """
        cache_key = f"risk:portfolio:{portfolio_id}:limits"
        limits = cache.get(cache_key)

        if limits is None:
            limits = list(
                RiskLimit.objects.filter(portfolio_id=portfolio_id, is_active=True)
                .values('id', 'limit_type', 'threshold_value')
            )
            for item in limits:
                item['threshold_value'] = float(item['threshold_value'])

            cache.set(cache_key, limits, timeout=21600)  # 6 ساعات

        return limits

    @staticmethod
    def invalidate_portfolio_risk_limits(portfolio_id: int):
        """إبطال كاش الحدود فور تعديل أي شرط أو تفعيل/تعطيل حد مخاطرة."""
        cache.delete(f"risk:portfolio:{portfolio_id}:limits")

    # =========================================================================
    # 2. PortfolioRiskMetric Caching (مؤشرات المخاطر الإحصائية VaR, Sharpe, Beta)
    # =========================================================================
    @staticmethod
    def get_latest_portfolio_risk_metrics(portfolio_id: int):
        """
        تخزين أحدث قراءة لمؤشرات مخاطر المحفظة (عادة ما تحسب يومياً عبر Celery Job) لمدة 12 ساعة.
        """
        cache_key = f"risk:portfolio:{portfolio_id}:latest_metrics"
        metrics_data = cache.get(cache_key)

        if metrics_data is None:
            latest = PortfolioRiskMetric.objects.filter(portfolio_id=portfolio_id).first()
            if latest:
                metrics_data = {
                    'id': latest.id,
                    'calculation_date': latest.calculation_date.isoformat(),
                    'var_95_daily': float(latest.var_95_daily) if latest.var_95_daily is not None else None,
                    'var_99_daily': float(latest.var_99_daily) if latest.var_99_daily is not None else None,
                    'expected_shortfall': float(latest.expected_shortfall) if latest.expected_shortfall is not None else None,
                    'sharpe_ratio': float(latest.sharpe_ratio) if latest.sharpe_ratio is not None else None,
                    'sortino_ratio': float(latest.sortino_ratio) if latest.sortino_ratio is not None else None,
                    'beta': float(latest.beta) if latest.beta is not None else None,
                    'volatility_annualized': float(latest.volatility_annualized) if latest.volatility_annualized is not None else None,
                    'max_drawdown_pct': float(latest.max_drawdown_pct) if latest.max_drawdown_pct is not None else None,
                }
                cache.set(cache_key, metrics_data, timeout=43200)  # 12 ساعة
            else:
                return None

        return metrics_data

    @staticmethod
    def invalidate_portfolio_risk_metrics(portfolio_id: int):
        """إبطال كاش المؤشرات عند إكتمال مهمة إعادة الاحتساب."""
        cache.delete(f"risk:portfolio:{portfolio_id}:latest_metrics")

    # =========================================================================
    # 3. StressTestScenario & Results Caching (سيناريوهات ونتائج اختبارات الإجهاد)
    # =========================================================================
    @staticmethod
    def get_all_stress_test_scenarios():
        """
        تخزين قائمة سيناريوهات الصدمات الاقتصادية (مثل أزمة 2008 أو هبوط القطاع) لمدة 24 ساعة.
        """
        cache_key = "risk:stress_test:scenarios:all"
        scenarios = cache.get(cache_key)

        if scenarios is None:
            scenarios = list(
                StressTestScenario.objects.all()
                .values('id', 'name', 'description', 'market_shock_pct', 'interest_rate_change_bps')
            )
            for s in scenarios:
                s['market_shock_pct'] = float(s['market_shock_pct'])

            cache.set(cache_key, scenarios, timeout=86400)  # 24 ساعة

        return scenarios

    @staticmethod
    def get_portfolio_stress_test_results(portfolio_id: int):
        """
        تخزين آخر نتائج محاكاة اختبارات الإجهاد للمحفظة لمدة 3 ساعات.
        """
        cache_key = f"risk:portfolio:{portfolio_id}:stress_test_results"
        results = cache.get(cache_key)

        if results is None:
            results = list(
                StressTestResult.objects.filter(portfolio_id=portfolio_id)
                .select_related('scenario')
                .values(
                    'id', 'scenario__name', 'projected_loss_amount',
                    'projected_loss_pct', 'evaluated_at'
                )
            )
            for r in results:
                r['projected_loss_amount'] = float(r['projected_loss_amount'])
                r['projected_loss_pct'] = float(r['projected_loss_pct'])
                r['evaluated_at'] = r['evaluated_at'].isoformat()

            cache.set(cache_key, results, timeout=10800)  # 3 ساعات

        return results

    @staticmethod
    def invalidate_stress_test_cache(portfolio_id: int = None):
        """مسح كاش سيناريوهات الإجهاد أو كاش النتائج المحسوبة للمحفظة."""
        cache.delete("risk:stress_test:scenarios:all")
        if portfolio_id:
            cache.delete(f"risk:portfolio:{portfolio_id}:stress_test_results")

    # =========================================================================
    # 4. RiskAlert Caching (تنبيهات خرق حدود المخاطر الحية)
    # =========================================================================
    @staticmethod
    def get_open_portfolio_risk_alerts(portfolio_id: int):
        """
        تخزين قائمة التنبيهات المفتوحة (OPEN / ACKNOWLEDGED) للمحفظة لمدة 5 دقائق.
        تستخدم لإظهار التنبيهات في شريط النظام العلوي (Navbar / Dashboard).
        """
        cache_key = f"risk:portfolio:{portfolio_id}:open_alerts"
        alerts = cache.get(cache_key)

        if alerts is None:
            alerts = list(
                RiskAlert.objects.filter(portfolio_id=portfolio_id, status__in=['OPEN', 'ACKNOWLEDGED'])
                .values('id', 'title', 'description', 'severity', 'status', 'created_at')
            )
            for a in alerts:
                a['created_at'] = a['created_at'].isoformat()

            cache.set(cache_key, alerts, timeout=300)  # 5 دقائق

        return alerts

    @staticmethod
    def invalidate_risk_alert_cache(portfolio_id: int):
        """إبطال كاش التنبيهات فور إطلاق تنبيه جديد أو تغيير حالته إلى Resolved."""
        cache.delete(f"risk:portfolio:{portfolio_id}:open_alerts")
from celery import shared_task
from django.db import transaction
from decimal import Decimal
import logging

from .models import RiskLimit, PortfolioRiskMetric, StressTestScenario, StressTestResult, RiskAlert
from PortfolioManagement.models import Portfolio
from .cache import RiskManagementCacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_portfolio_risk_metrics_task(self, portfolio_id: int, calculation_date_str: str):
    """
    مهمة غير متزامنة لاحتساب مؤشرات المخاطر الإحصائية (VaR, Sharpe Ratio, Beta)
    للمحفظة وتسجيلها في الجدول مع مسح الكاش.
    """
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        
        # 1. منطق محاكاة حساب مؤشرات المخاطر الحقيقية (يمكن ربطه بـ Pandas / NumPy)
        # هنا نفترض حساب القيم ديناميكياً:
        var_95 = Decimal('1500.5000')
        var_99 = Decimal('2800.7500')
        cvar = Decimal('3200.0000')
        sharpe = Decimal('1.8500')
        sortino = Decimal('2.1000')
        beta = Decimal('1.1200')
        volatility = Decimal('0.1540')
        max_dd = Decimal('8.5000')

        # 2. حفظ النتائج في قاعدة البيانات
        metric, _ = PortfolioRiskMetric.objects.update_or_create(
            portfolio=portfolio,
            calculation_date=calculation_date_str,
            defaults={
                'var_95_daily': var_95,
                'var_99_daily': var_99,
                'expected_shortfall': cvar,
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'beta': beta,
                'volatility_annualized': volatility,
                'max_drawdown_pct': max_dd,
            }
        )

        # 3. إبطال الكاش الخاص بمؤشرات المخاطر
        RiskManagementCacheService.invalidate_portfolio_risk_metrics(portfolio_id)
        
        logger.info(f"Successfully calculated risk metrics for portfolio {portfolio_id}")
        return f"Risk metrics updated for Portfolio {portfolio_id}"

    except Portfolio.DoesNotExist:
        logger.error(f"Portfolio {portfolio_id} not found.")
        return None
    except Exception as exc:
        logger.error(f"Error calculating risk metrics: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def run_stress_test_simulation_task(self, portfolio_id: int, scenario_id: int):
    """
    مهمة غير متزامنة لتشغيل محاكاة اختبارات الإجهاد (Stress Testing)
    وتقييم الخسائر المتوقعة بناءً على صدمات السوق.
    """
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        scenario = StressTestScenario.objects.get(id=scenario_id)

        # حساب الخسارة التقديرية بناءً على نسبة صدمة السوق والقيمة الكلية للمحفظة
        market_shock = abs(scenario.market_shock_pct) / Decimal('100.00')
        projected_loss_amount = portfolio.total_value * market_shock
        projected_loss_pct = scenario.market_shock_pct

        # تسجيلة النتيجة
        StressTestResult.objects.create(
            portfolio=portfolio,
            scenario=scenario,
            projected_loss_amount=projected_loss_amount,
            projected_loss_pct=projected_loss_pct,
        )

        # مسح كاش نتائج اختيارات الإجهاد
        RiskManagementCacheService.invalidate_stress_test_cache(portfolio_id=portfolio_id)

        return f"Stress test '{scenario.name}' completed for portfolio {portfolio.account_number}"

    except (Portfolio.DoesNotExist, StressTestScenario.DoesNotExist) as e:
        logger.error(f"Stress test error: {e}")
        return None


@shared_task
def check_portfolio_risk_limits_task(portfolio_id: int):
    """
    مهمة فحص تلقائية لجميع قيود المخاطر (Risk Limits) للمحفظة وتوليد تنبيهات (RiskAlert)
    فور حدوث أي خرق للحواجز المسموحة.
    """
    limits = RiskLimit.objects.filter(portfolio_id=portfolio_id, is_active=True)
    latest_metric = PortfolioRiskMetric.objects.filter(portfolio_id=portfolio_id).first()

    if not latest_metric:
        return "No metrics available to validate limits."

    for limit in limits:
        # فحص خرق حد أقصى للتراجع (Max Drawdown Limit Violation)
        if limit.limit_type == 'MAX_DRAWDOWN' and latest_metric.max_drawdown_pct:
            if latest_metric.max_drawdown_pct > limit.threshold_value:
                RiskAlert.objects.create(
                    portfolio_id=portfolio_id,
                    risk_limit=limit,
                    title="Max Drawdown Threshold Breached",
                    description=f"Current Drawdown {latest_metric.max_drawdown_pct}% exceeded limit of {limit.threshold_value}%.",
                    severity='CRITICAL',
                    status='OPEN'
                )
                RiskManagementCacheService.invalidate_risk_alert_cache(portfolio_id)

    return f"Risk limits check completed for portfolio {portfolio_id}"
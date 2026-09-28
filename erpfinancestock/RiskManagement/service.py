from datetime import date
from .tasks import (
    calculate_portfolio_risk_metrics_task,
    run_stress_test_simulation_task,
    check_portfolio_risk_limits_task,
)
from .cache import RiskManagementCacheService


class RiskManagementService:
    """
    طبقة الخدمات (Service Layer) الخاصة بقسم إدارة المخاطر.
    تقوم بتنظيم استدعاءات مهام Celery وقراءة الكاش الاحترافي.
    """

    @staticmethod
    def trigger_risk_metrics_calculation(portfolio_id: int, calc_date: date = None):
        """
        طلب حساب مؤشرات المخاطر وإرسالها لـ Celery Queue للعمل في الخلفية.
        """
        if calc_date is None:
            calc_date = date.today()

        # إرسال المهمة للطابور غير المتناغم Celery
        task = calculate_portfolio_risk_metrics_task.delay(
            portfolio_id=portfolio_id,
            calculation_date_str=calc_date.isoformat()
        )
        return {"status": "processing", "task_id": task.id}

    @staticmethod
    def run_stress_test(portfolio_id: int, scenario_id: int):
        """
        بدء تنفيذ محاكاة اختبار الإجهاد في الخلفية.
        """
        task = run_stress_test_simulation_task.delay(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id
        )
        return {"status": "simulation_queued", "task_id": task.id}

    @staticmethod
    def evaluate_limits_and_alerts(portfolio_id: int):
        """
        فحص القيود وإطلاق التنبيهات عبر Celery.
        """
        task = check_portfolio_risk_limits_task.delay(portfolio_id=portfolio_id)
        return {"status": "limit_check_queued", "task_id": task.id}

    @staticmethod
    def get_portfolio_risk_dashboard(portfolio_id: int):
        """
        جلب بيانات لوحة تحكم المخاطر فوراً وبسرعة فائقة من Redis Cache.
        """
        limits = RiskManagementCacheService.get_portfolio_risk_limits(portfolio_id)
        metrics = RiskManagementCacheService.get_latest_portfolio_risk_metrics(portfolio_id)
        alerts = RiskManagementCacheService.get_open_portfolio_risk_alerts(portfolio_id)

        return {
            "limits": limits,
            "latest_metrics": metrics,
            "active_alerts": alerts,
        }

    # the operation logic on the models 

    from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from PortfolioManagement.models import Portfolio
from .models import (
    RiskLimit,
    PortfolioRiskMetric,
    StressTestScenario,
    StressTestResult,
    RiskAlert,
)
from .schemas import (
    RiskLimitCreateSchema,
    RiskLimitUpdateSchema,
    PortfolioRiskMetricCreateSchema,
    StressTestScenarioCreateSchema,
    StressTestScenarioUpdateSchema,
    StressTestResultCreateSchema,
    RiskAlertCreateSchema,
    RiskAlertUpdateSchema,
)

User = get_user_model()


class RiskManagementService:

    # --- Risk Limit Operations ---
    @classmethod
    @transaction.atomic
    def create_risk_limit(cls, data: RiskLimitCreateSchema) -> RiskLimit:
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)
        limit, _ = RiskLimit.objects.update_or_create(
            portfolio=portfolio,
            limit_type=data.limit_type,
            defaults={
                "threshold_value": data.threshold_value,
                "is_active": data.is_active,
            }
        )
        return limit

    @staticmethod
    def list_risk_limits(portfolio_id: Optional[int] = None) -> List[RiskLimit]:
        qs = RiskLimit.objects.select_related("portfolio").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        return qs

    @classmethod
    @transaction.atomic
    def update_risk_limit(cls, limit_id: int, data: RiskLimitUpdateSchema) -> RiskLimit:
        limit = get_object_or_404(RiskLimit, id=limit_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(limit, key, value)
        limit.save()
        return limit

    # --- Portfolio Risk Metric Operations ---
    @classmethod
    @transaction.atomic
    def create_risk_metric(cls, data: PortfolioRiskMetricCreateSchema) -> PortfolioRiskMetric:
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)
        metric, _ = PortfolioRiskMetric.objects.update_or_create(
            portfolio=portfolio,
            calculation_date=data.calculation_date,
            defaults={
                "var_95_daily": data.var_95_daily,
                "var_99_daily": data.var_99_daily,
                "expected_shortfall": data.expected_shortfall,
                "sharpe_ratio": data.sharpe_ratio,
                "sortino_ratio": data.sortino_ratio,
                "beta": data.beta,
                "volatility_annualized": data.volatility_annualized,
                "max_drawdown_pct": data.max_drawdown_pct,
            }
        )
        return metric

    @staticmethod
    def list_risk_metrics(portfolio_id: Optional[int] = None) -> List[PortfolioRiskMetric]:
        qs = PortfolioRiskMetric.objects.select_related("portfolio").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        return qs

    # --- Stress Test Scenario Operations ---
    @classmethod
    @transaction.atomic
    def create_stress_scenario(cls, data: StressTestScenarioCreateSchema) -> StressTestScenario:
        return StressTestScenario.objects.create(
            name=data.name,
            description=data.description,
            market_shock_pct=data.market_shock_pct,
            interest_rate_change_bps=data.interest_rate_change_bps,
        )

    @staticmethod
    def list_stress_scenarios() -> List[StressTestScenario]:
        return StressTestScenario.objects.all()

    @classmethod
    @transaction.atomic
    def update_stress_scenario(cls, scenario_id: int, data: StressTestScenarioUpdateSchema) -> StressTestScenario:
        scenario = get_object_or_404(StressTestScenario, id=scenario_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(scenario, key, value)
        scenario.save()
        return scenario

    # --- Stress Test Result Operations ---
    @classmethod
    @transaction.atomic
    def create_stress_result(cls, data: StressTestResultCreateSchema) -> StressTestResult:
        scenario = get_object_or_404(StressTestScenario, id=data.scenario_id)
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)

        return StressTestResult.objects.create(
            scenario=scenario,
            portfolio=portfolio,
            projected_loss_amount=data.projected_loss_amount,
            projected_loss_pct=data.projected_loss_pct,
        )

    @staticmethod
    def list_stress_results(portfolio_id: Optional[int] = None, scenario_id: Optional[int] = None) -> List[StressTestResult]:
        qs = StressTestResult.objects.select_related("scenario", "portfolio").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        if scenario_id:
            qs = qs.filter(scenario_id=scenario_id)
        return qs

    # --- Risk Alert Operations ---
    @classmethod
    @transaction.atomic
    def create_risk_alert(cls, data: RiskAlertCreateSchema) -> RiskAlert:
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)
        risk_limit = get_object_or_404(RiskLimit, id=data.risk_limit_id) if data.risk_limit_id else None

        return RiskAlert.objects.create(
            portfolio=portfolio,
            risk_limit=risk_limit,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=data.status,
        )

    @staticmethod
    def list_risk_alerts(portfolio_id: Optional[int] = None, status: Optional[str] = None) -> List[RiskAlert]:
        qs = RiskAlert.objects.select_related("portfolio", "risk_limit", "acknowledged_by").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    @classmethod
    @transaction.atomic
    def update_risk_alert(cls, alert_id: int, user: User, data: RiskAlertUpdateSchema) -> RiskAlert:
        alert = get_object_or_404(RiskAlert, id=alert_id)
        update_data = data.dict(exclude_unset=True)

        if "status" in update_data and update_data["status"] == 'RESOLVED' and not alert.resolved_at:
            alert.resolved_at = timezone.now()
            alert.acknowledged_by = user

        for key, value in update_data.items():
            setattr(alert, key, value)

        alert.save()
        return alert
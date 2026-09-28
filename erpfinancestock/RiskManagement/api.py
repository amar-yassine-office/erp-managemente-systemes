from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
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
    RiskLimitOutSchema,
    PortfolioRiskMetricCreateSchema,
    PortfolioRiskMetricOutSchema,
    StressTestScenarioCreateSchema,
    StressTestScenarioUpdateSchema,
    StressTestScenarioOutSchema,
    StressTestResultCreateSchema,
    StressTestResultOutSchema,
    RiskAlertCreateSchema,
    RiskAlertUpdateSchema,
    RiskAlertOutSchema,
)
from .service import RiskManagementService

# =====================================================================
# 1. RISK LIMIT ENDPOINTS
# =====================================================================

@router.post("/limits/", response={201: RiskLimitOutSchema})
def create_risk_limit(request, payload: RiskLimitCreateSchema):
    return 201, RiskManagementService.create_risk_limit(data=payload)

@router.get("/limits/", response=List[RiskLimitOutSchema])
def list_risk_limits(request, portfolio_id: Optional[int] = Query(None)):
    return RiskManagementService.list_risk_limits(portfolio_id=portfolio_id)

@router.patch("/limits/{limit_id}/", response=RiskLimitOutSchema)
def update_risk_limit(request, limit_id: int, payload: RiskLimitUpdateSchema):
    return RiskManagementService.update_risk_limit(limit_id=limit_id, data=payload)


# =====================================================================
# 2. PORTFOLIO RISK METRIC ENDPOINTS
# =====================================================================

@router.post("/metrics/", response={201: PortfolioRiskMetricOutSchema})
def create_risk_metric(request, payload: PortfolioRiskMetricCreateSchema):
    return 201, RiskManagementService.create_risk_metric(data=payload)

@router.get("/metrics/", response=List[PortfolioRiskMetricOutSchema])
def list_risk_metrics(request, portfolio_id: Optional[int] = Query(None)):
    return RiskManagementService.list_risk_metrics(portfolio_id=portfolio_id)


# =====================================================================
# 3. STRESS TEST SCENARIO ENDPOINTS
# =====================================================================

@router.post("/scenarios/", response={201: StressTestScenarioOutSchema})
def create_stress_scenario(request, payload: StressTestScenarioCreateSchema):
    return 201, RiskManagementService.create_stress_scenario(data=payload)

@router.get("/scenarios/", response=List[StressTestScenarioOutSchema])
def list_stress_scenarios(request):
    return RiskManagementService.list_stress_scenarios()

@router.patch("/scenarios/{scenario_id}/", response=StressTestScenarioOutSchema)
def update_stress_scenario(request, scenario_id: int, payload: StressTestScenarioUpdateSchema):
    return RiskManagementService.update_stress_scenario(scenario_id=scenario_id, data=payload)


# =====================================================================
# 4. STRESS TEST RESULT ENDPOINTS
# =====================================================================

@router.post("/stress-results/", response={201: StressTestResultOutSchema})
def create_stress_result(request, payload: StressTestResultCreateSchema):
    return 201, RiskManagementService.create_stress_result(data=payload)

@router.get("/stress-results/", response=List[StressTestResultOutSchema])
def list_stress_results(request, portfolio_id: Optional[int] = Query(None), scenario_id: Optional[int] = Query(None)):
    return RiskManagementService.list_stress_results(portfolio_id=portfolio_id, scenario_id=scenario_id)


# =====================================================================
# 5. RISK ALERT ENDPOINTS
# =====================================================================

@router.post("/alerts/", response={201: RiskAlertOutSchema})
def create_risk_alert(request, payload: RiskAlertCreateSchema):
    return 201, RiskManagementService.create_risk_alert(data=payload)

@router.get("/alerts/", response=List[RiskAlertOutSchema])
def list_risk_alerts(request, portfolio_id: Optional[int] = Query(None), status: Optional[str] = Query(None)):
    return RiskManagementService.list_risk_alerts(portfolio_id=portfolio_id, status=status)

@router.patch("/alerts/{alert_id}/", response=RiskAlertOutSchema)
def update_risk_alert(request, alert_id: int, payload: RiskAlertUpdateSchema):
    return RiskManagementService.update_risk_alert(alert_id=alert_id, user=request.user, data=payload)
from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
from .models import (
    MarketAsset,
    ResearchReport,
    AnalystRecommendation,
    FinancialMetric,
    MarketSentiment,
)
from .schemas import (
    MarketAssetCreateSchema,
    MarketAssetUpdateSchema,
    MarketAssetOutSchema,
    ResearchReportCreateSchema,
    ResearchReportUpdateSchema,
    ResearchReportOutSchema,
    AnalystRecommendationCreateSchema,
    AnalystRecommendationOutSchema,
    FinancialMetricCreateSchema,
    FinancialMetricOutSchema,
    MarketSentimentCreateSchema,
    MarketSentimentOutSchema,
)
from .service import ResearchAnalyticsService

# =====================================================================
# 1. MARKET ASSET ENDPOINTS
# =====================================================================

@router.post("/assets/", response={201: MarketAssetOutSchema})
def create_market_asset(request, payload: MarketAssetCreateSchema):
    return 201, ResearchAnalyticsService.create_market_asset(data=payload)

@router.get("/assets/", response=List[MarketAssetOutSchema])
def list_market_assets(request, asset_class: Optional[str] = Query(None), is_active: Optional[bool] = Query(None)):
    return ResearchAnalyticsService.list_market_assets(asset_class=asset_class, is_active=is_active)

@router.get("/assets/{asset_id}/", response=MarketAssetOutSchema)
def get_market_asset(request, asset_id: int):
    return get_object_or_404(MarketAsset, id=asset_id)

@router.patch("/assets/{asset_id}/", response=MarketAssetOutSchema)
def update_market_asset(request, asset_id: int, payload: MarketAssetUpdateSchema):
    return ResearchAnalyticsService.update_market_asset(asset_id=asset_id, data=payload)


# =====================================================================
# 2. RESEARCH REPORT ENDPOINTS
# =====================================================================

@router.post("/reports/", response={201: ResearchReportOutSchema})
def create_research_report(request, payload: ResearchReportCreateSchema):
    return 201, ResearchAnalyticsService.create_research_report(author=request.user, data=payload)

@router.get("/reports/", response=List[ResearchReportOutSchema])
def list_research_reports(request, status: Optional[str] = Query(None), asset_id: Optional[int] = Query(None)):
    return ResearchAnalyticsService.list_research_reports(status=status, asset_id=asset_id)

@router.get("/reports/{report_id}/", response=ResearchReportOutSchema)
def get_research_report(request, report_id: int):
    return get_object_or_404(ResearchReport.objects.select_related("author", "asset"), id=report_id)

@router.patch("/reports/{report_id}/", response=ResearchReportOutSchema)
def update_research_report(request, report_id: int, payload: ResearchReportUpdateSchema):
    return ResearchAnalyticsService.update_research_report(report_id=report_id, data=payload)


# =====================================================================
# 3. ANALYST RECOMMENDATION ENDPOINTS
# =====================================================================

@router.post("/recommendations/", response={201: AnalystRecommendationOutSchema})
def create_analyst_recommendation(request, payload: AnalystRecommendationCreateSchema):
    return 201, ResearchAnalyticsService.create_analyst_recommendation(analyst=request.user, data=payload)

@router.get("/recommendations/", response=List[AnalystRecommendationOutSchema])
def list_recommendations(request, asset_id: Optional[int] = Query(None), rating: Optional[str] = Query(None)):
    return ResearchAnalyticsService.list_recommendations(asset_id=asset_id, rating=rating)


# =====================================================================
# 4. FINANCIAL METRIC ENDPOINTS
# =====================================================================

@router.post("/metrics/", response={201: FinancialMetricOutSchema})
def create_financial_metric(request, payload: FinancialMetricCreateSchema):
    return 201, ResearchAnalyticsService.create_financial_metric(data=payload)

@router.get("/metrics/", response=List[FinancialMetricOutSchema])
def list_financial_metrics(request, asset_id: Optional[int] = Query(None)):
    return ResearchAnalyticsService.list_financial_metrics(asset_id=asset_id)


# =====================================================================
# 5. MARKET SENTIMENT ENDPOINTS
# =====================================================================

@router.post("/sentiments/", response={201: MarketSentimentOutSchema})
def create_market_sentiment(request, payload: MarketSentimentCreateSchema):
    return 201, ResearchAnalyticsService.create_market_sentiment(data=payload)

@router.get("/sentiments/", response=List[MarketSentimentOutSchema])
def list_market_sentiments(request, asset_id: Optional[int] = Query(None)):
    return ResearchAnalyticsService.list_market_sentiments(asset_id=asset_id)
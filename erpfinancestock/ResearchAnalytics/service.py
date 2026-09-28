from datetime import date
from typing import Dict, Any

# استيراد المهام من tasks.py
from .tasks import (
    sync_market_asset_financials_task,
    aggregate_market_sentiment_task,
    publish_research_report_task,
    calculate_consensus_analyst_rating_task,
)
from .cache import ResearchAnalyticsCacheService


class ResearchAnalyticsService:
    """
    طبقة الخدمات (Service Layer) لقسم الأبحاث والتحليلات المالية.
    تتعامل مع المهام غير المتزامنة وتدفق البيانات من وإلى الكاش.
    """

    @staticmethod
    def sync_asset_financials(asset_id: int, period_date: date, metrics_data: Dict[str, Any]):
        """
        إرسال مهمة تحديث البيانات المالية للأصل لتنفذ في الخلفية.
        """
        task = sync_market_asset_financials_task.delay(
            asset_id=asset_id,
            period_date_str=period_date.isoformat(),
            metrics_data=metrics_data
        )
        return {"status": "processing", "task_id": task.id}

    @staticmethod
    def evaluate_sentiment(asset_id: int, sentiment_score: float, source_count: int, summary: str):
        """
        إرسال مهمة تحليل مشاعر السوق للعمل عبر Celery Worker.
        """
        task = aggregate_market_sentiment_task.delay(
            asset_id=asset_id,
            sentiment_score_val=sentiment_score,
            source_count=source_count,
            summary_text=summary
        )
        return {"status": "queued", "task_id": task.id}

    @staticmethod
    def publish_report(report_id: int):
        """
        إطلاق مهمة نشر التقرير البحثي غير المتزامنة.
        """
        task = publish_research_report_task.delay(report_id=report_id)
        return {"status": "publishing_queued", "task_id": task.id}

    @staticmethod
    def recalculate_consensus(asset_id: int):
        """
        إطلاق إعادة حساب متوسط التوصيات والسعر المستهدف عبر Celery.
        """
        task = calculate_consensus_analyst_rating_task.delay(asset_id=asset_id)
        return {"status": "calculation_queued", "task_id": task.id}

    @staticmethod
    def get_asset_analytics_dashboard(asset_id: int):
        """
        استرجاع شاشة تحليلات الأصل فوراً وسريعا من الـ Redis Cache.
        """
        financials = ResearchAnalyticsCacheService.get_latest_financial_metrics(asset_id)
        sentiment = ResearchAnalyticsCacheService.get_latest_market_sentiment(asset_id)
        consensus = ResearchAnalyticsCacheService.get_consensus_rating_cache(asset_id)

        return {
            "asset_id": asset_id,
            "financial_metrics": financials,
            "market_sentiment": sentiment,
            "analyst_consensus": consensus,
        }
    # the operations logic on the models 
    from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

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
    ResearchReportCreateSchema,
    ResearchReportUpdateSchema,
    AnalystRecommendationCreateSchema,
    FinancialMetricCreateSchema,
    MarketSentimentCreateSchema,
)

User = get_user_model()


class ResearchAnalyticsService:

    # --- Market Asset Operations ---
    @classmethod
    @transaction.atomic
    def create_market_asset(cls, data: MarketAssetCreateSchema) -> MarketAsset:
        return MarketAsset.objects.create(
            symbol=data.symbol.upper(),
            name=data.name,
            asset_class=data.asset_class,
            sector=data.sector or "",
            exchange=data.exchange or "",
            is_active=data.is_active,
        )

    @staticmethod
    def list_market_assets(asset_class: Optional[str] = None, is_active: Optional[bool] = None) -> List[MarketAsset]:
        qs = MarketAsset.objects.all()
        if asset_class:
            qs = qs.filter(asset_class=asset_class)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    @classmethod
    @transaction.atomic
    def update_market_asset(cls, asset_id: int, data: MarketAssetUpdateSchema) -> MarketAsset:
        asset = get_object_or_404(MarketAsset, id=asset_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)
        asset.save()
        return asset

    # --- Research Report Operations ---
    @classmethod
    @transaction.atomic
    def create_research_report(cls, author: User, data: ResearchReportCreateSchema) -> ResearchReport:
        asset = get_object_or_404(MarketAsset, id=data.asset_id) if data.asset_id else None
        published_at = data.published_at
        if data.status == 'PUBLISHED' and not published_at:
            published_at = timezone.now()

        return ResearchReport.objects.create(
            author=author,
            asset=asset,
            title=data.title,
            summary=data.summary,
            content=data.content,
            status=data.status,
            is_premium=data.is_premium,
            published_at=published_at,
        )

    @staticmethod
    def list_research_reports(status: Optional[str] = None, asset_id: Optional[int] = None) -> List[ResearchReport]:
        qs = ResearchReport.objects.select_related("author", "asset").all()
        if status:
            qs = qs.filter(status=status)
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs

    @classmethod
    @transaction.atomic
    def update_research_report(cls, report_id: int, data: ResearchReportUpdateSchema) -> ResearchReport:
        report = get_object_or_404(ResearchReport, id=report_id)
        update_data = data.dict(exclude_unset=True)

        if "asset_id" in update_data:
            ast_id = update_data.pop("asset_id")
            report.asset = get_object_or_404(MarketAsset, id=ast_id) if ast_id else None

        if "status" in update_data and update_data["status"] == 'PUBLISHED' and not report.published_at:
            report.published_at = timezone.now()

        for key, value in update_data.items():
            setattr(report, key, value)

        report.save()
        return report

    # --- Analyst Recommendation Operations ---
    @classmethod
    @transaction.atomic
    def create_analyst_recommendation(cls, analyst: User, data: AnalystRecommendationCreateSchema) -> AnalystRecommendation:
        asset = get_object_or_404(MarketAsset, id=data.asset_id)
        report = get_object_or_404(ResearchReport, id=data.report_id) if data.report_id else None

        return AnalystRecommendation.objects.create(
            analyst=analyst,
            asset=asset,
            report=report,
            rating=data.rating,
            current_price_at_rating=data.current_price_at_rating,
            target_price=data.target_price,
            time_horizon_months=data.time_horizon_months,
            is_active=data.is_active,
        )

    @staticmethod
    def list_recommendations(asset_id: Optional[int] = None, rating: Optional[str] = None) -> List[AnalystRecommendation]:
        qs = AnalystRecommendation.objects.select_related("analyst", "asset", "report").all()
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        if rating:
            qs = qs.filter(rating=rating)
        return qs

    # --- Financial Metric Operations ---
    @classmethod
    @transaction.atomic
    def create_financial_metric(cls, data: FinancialMetricCreateSchema) -> FinancialMetric:
        asset = get_object_or_404(MarketAsset, id=data.asset_id)
        metric, _ = FinancialMetric.objects.update_or_create(
            asset=asset,
            period_date=data.period_date,
            defaults={
                "pe_ratio": data.pe_ratio,
                "pb_ratio": data.pb_ratio,
                "eps": data.eps,
                "debt_to_equity": data.debt_to_equity,
                "roe_pct": data.roe_pct,
                "free_cash_flow": data.free_cash_flow,
            }
        )
        return metric

    @staticmethod
    def list_financial_metrics(asset_id: Optional[int] = None) -> List[FinancialMetric]:
        qs = FinancialMetric.objects.select_related("asset").all()
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs

    # --- Market Sentiment Operations ---
    @classmethod
    @transaction.atomic
    def create_market_sentiment(cls, data: MarketSentimentCreateSchema) -> MarketSentiment:
        asset = get_object_or_404(MarketAsset, id=data.asset_id)
        return MarketSentiment.objects.create(
            asset=asset,
            sentiment_score=data.sentiment_score,
            label=data.label,
            news_source_count=data.news_source_count,
            summary=data.summary,
        )

    @staticmethod
    def list_market_sentiments(asset_id: Optional[int] = None) -> List[MarketSentiment]:
        qs = MarketSentiment.objects.select_related("asset").all()
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs
from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Count
from decimal import Decimal
import logging

from .models import (
    MarketAsset,
    ResearchReport,
    AnalystRecommendation,
    FinancialMetric,
    MarketSentiment,
)
from .cache import ResearchAnalyticsCacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_market_asset_financials_task(self, asset_id: int, period_date_str: str, metrics_data: dict):
    """
    مهمة غير متزامنة لمزامنة وتحديث المؤشرات المالية الأساسية (P/E, EPS, Free Cash Flow) للأصول.
    """
    try:
        asset = MarketAsset.objects.get(id=asset_id)
        
        metric, created = FinancialMetric.objects.update_or_create(
            asset=asset,
            period_date=period_date_str,
            defaults={
                'pe_ratio': metrics_data.get('pe_ratio'),
                'pb_ratio': metrics_data.get('pb_ratio'),
                'eps': metrics_data.get('eps'),
                'debt_to_equity': metrics_data.get('debt_to_equity'),
                'roe_pct': metrics_data.get('roe_pct'),
                'free_cash_flow': metrics_data.get('free_cash_flow'),
            }
        )

        # إبطال الكاش الخاص بالمؤشرات المالية للأصل
        ResearchAnalyticsCacheService.invalidate_financial_metrics_cache(asset_id)
        
        logger.info(f"Successfully synced financial metrics for asset {asset.symbol}")
        return f"Financial metrics updated for {asset.symbol}"

    except MarketAsset.DoesNotExist:
        logger.error(f"MarketAsset with ID {asset_id} does not exist.")
        return None
    except Exception as exc:
        logger.error(f"Error syncing financial metrics for asset {asset_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def aggregate_market_sentiment_task(self, asset_id: int, sentiment_score_val: float, source_count: int, summary_text: str):
    """
    مهمة حساب ومعالجة مشاعر السوق (Market Sentiment) بناءً على الأخبار وتحليلات التواصل الاجتماعي.
    """
    try:
        asset = MarketAsset.objects.get(id=asset_id)
        score = Decimal(str(sentiment_score_val))

        # تحديد تصنيف المشاعر تلقائياً بناءً على الدرجة
        if score >= Decimal('0.25'):
            label = 'BULLISH'
        elif score <= Decimal('-0.25'):
            label = 'BEARISH'
        else:
            label = 'NEUTRAL'

        MarketSentiment.objects.create(
            asset=asset,
            sentiment_score=score,
            label=label,
            news_source_count=source_count,
            summary=summary_text
        )

        # إبطال الكاش الخاص بمعنويات السوق
        ResearchAnalyticsCacheService.invalidate_market_sentiment_cache(asset_id)

        return f"Sentiment evaluated for {asset.symbol}: {label} ({score})"

    except MarketAsset.DoesNotExist:
        logger.error(f"MarketAsset {asset_id} not found for sentiment task.")
        return None


@shared_task
def publish_research_report_task(report_id: int):
    """
    مهمة غير متزامنة لنشر التقارير البحثية وتغيير حالتها مع تحديث تاريخ النشر والكاش.
    """
    try:
        report = ResearchReport.objects.get(id=report_id)
        report.status = 'PUBLISHED'
        report.published_at = timezone.now()
        report.save(update_fields=['status', 'published_at', 'updated_at'])

        # إبطال الكاش الخاص بالتقارير
        ResearchAnalyticsCacheService.invalidate_reports_cache(asset_id=report.asset_id)

        return f"Research Report '{report.title}' published successfully."
    except ResearchReport.DoesNotExist:
        return f"Report {report_id} not found."


@shared_task
def calculate_consensus_analyst_rating_task(asset_id: int):
    """
    مهمة تجميعية لاحتساب متوسط السعر المستهدف (Consensus Target Price) وتوصيات المحللين للأصل.
    """
    recs = AnalystRecommendation.objects.filter(asset_id=asset_id, is_active=True)
    if not recs.exists():
        return f"No active recommendations for asset {asset_id}"

    avg_target = recs.aggregate(Avg('target_price'))['target_price__avg']
    total_recs = recs.count()

    # تحديث الكاش الاحترافي بالإحصائيات المجمعة مباشرة
    ResearchAnalyticsCacheService.set_consensus_rating_cache(
        asset_id=asset_id,
        data={
            'average_target_price': str(avg_target),
            'total_analysts': total_recs,
            'last_updated': timezone.now().isoformat()
        }
    )

    return f"Consensus calculated for asset {asset_id}: Avg Target = {avg_target}"
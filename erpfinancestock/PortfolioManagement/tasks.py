from celery import shared_task
from django.db import transaction
from django.db.models import Sum, F
from decimal import Decimal
import logging

from .models import Portfolio, PortfolioPosition, PortfolioPerformance, AssetAllocation
from .cache import PortfolioManagementCacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def recalculate_portfolio_total_value_task(self, portfolio_id: int):
    """
    مهمة غير متزامنة لاحتساب القيمة الإجمالية للمحفظة (Total Value)
    بناءً على النقد المتاح والقيمة السوقية الحالية لجميع المراكز (Positions).
    """
    try:
        with transaction.atomic():
            portfolio = Portfolio.objects.select_for_update().get(id=portfolio_id)
            
            # حساب القيمة السوقية الإجمالية للمراكز (الكمية × السعر الحالي)
            positions_value = portfolio.positions.aggregate(
                total_market_value=Sum(F('quantity') * F('current_price'))
            )['total_market_value'] or Decimal('0.0000')

            # القيمة الكلية = الرصيد النقدي + قيمة الأسهم/الأصول
            portfolio.total_value = portfolio.cash_balance + positions_value
            portfolio.save(update_fields=['total_value', 'updated_at'])

        # إبطال كاش المحفظة لتحديث البيانات فوراً للعميل
        PortfolioManagementCacheService.invalidate_portfolio_cache(portfolio_id)

        logger.info(f"Successfully recalculated total value for Portfolio {portfolio_id}: {portfolio.total_value}")
        return str(portfolio.total_value)

    except Portfolio.DoesNotExist:
        logger.error(f"Portfolio {portfolio_id} not found.")
        return None
    except Exception as exc:
        logger.error(f"Error recalculating portfolio value: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def update_position_market_prices_task(self, symbol: str, new_price_str: str):
    """
    مهمة تحديث السعر الحالي لجميع المراكز المالية لحامل الأسهم وتحديث قيم محافظهم في الخلفية.
    """
    try:
        new_price = Decimal(new_price_str)
        updated_count = PortfolioPosition.objects.filter(symbol=symbol).update(current_price=new_price)

        # جلب جميع المحافظ التأثرة بالتعديل لإعادة حساب قيمتها الإجمالية
        affected_portfolio_ids = PortfolioPosition.objects.filter(symbol=symbol).values_list('portfolio_id', flat=True).distinct()

        for p_id in affected_portfolio_ids:
            # استدعاء مهمة الحساب لكل محفظة
            recalculate_portfolio_total_value_task.delay(portfolio_id=p_id)

        return f"Updated price for symbol {symbol} across {updated_count} positions."

    except Exception as exc:
        logger.error(f"Error updating prices for {symbol}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def record_daily_portfolio_performance_task(portfolio_id: int, date_str: str):
    """
    مهمة احتساب وتسجيل العائد اليومي وصافي قيمة الأصول (NAV) للمحفظة.
    """
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        current_nav = portfolio.total_value

        # جلب آخر سجل أداء سابق للحساب
        previous_record = PortfolioPerformance.objects.filter(
            portfolio=portfolio,
            date__lt=date_str
        ).order_by('-date').first()

        if previous_record and previous_record.nav_value > Decimal('0.0000'):
            daily_return = ((current_nav - previous_record.nav_value) / previous_record.nav_value) * Decimal('100.00')
        else:
            daily_return = Decimal('0.0000')

        PortfolioPerformance.objects.update_or_create(
            portfolio=portfolio,
            date=date_str,
            defaults={
                'nav_value': current_nav,
                'daily_return_pct': daily_return,
            }
        )

        # مسح الكاش الخاص بالسجل التاريخي للمحفظة
        PortfolioManagementCacheService.invalidate_performance_cache(portfolio_id)

        return f"Performance recorded for Portfolio {portfolio.account_number} on {date_str}"

    except Portfolio.DoesNotExist:
        return f"Portfolio {portfolio_id} not found."


@shared_task
def check_rebalancing_needed_task(portfolio_id: int):
    """
    مهمة فحص انحراف توزيع الأصول (Asset Allocation Drift) ومقارنتها بالاستراتيجية المستهدفة.
    """
    try:
        portfolio = Portfolio.objects.select_related('strategy').get(id=portfolio_id)
        if not portfolio.strategy or portfolio.total_value == Decimal('0.0000'):
            return "No strategy or zero value."

        # حساب النسبة الحالية للنقد
        cash_pct = (portfolio.cash_balance / portfolio.total_value) * Decimal('100.00')
        
        # تخزين نتيجة الفحص في الكاش لتظهر في لوحة التحكم
        PortfolioManagementCacheService.set_rebalance_status_cache(
            portfolio_id=portfolio_id,
            data={
                'current_cash_pct': str(cash_pct),
                'target_cash_pct': str(portfolio.strategy.target_cash_pct),
                'rebalance_required': abs(cash_pct - portfolio.strategy.target_cash_pct) > Decimal('5.00')
            }
        )

        return f"Rebalancing check completed for portfolio {portfolio_id}"

    except Portfolio.DoesNotExist:
        return f"Portfolio {portfolio_id} not found."
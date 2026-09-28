from datetime import date
from decimal import Decimal
from typing import Dict, Any

# استيراد المهام المباشر من tasks.py
from .tasks import (
    recalculate_portfolio_total_value_task,
    update_position_market_prices_task,
    record_daily_portfolio_performance_task,
    check_rebalancing_needed_task,
)
from .cache import PortfolioManagementCacheService


class PortfolioManagementService:
    """
    طبقة الخدمات (Service Layer) الخاصة بإدارة المحافظ والمراكز المالية.
    تدير عمليات Celery الكثيفة والقراءة من طبقة Caching.
    """

    @staticmethod
    def trigger_portfolio_recalculation(portfolio_id: int):
        """
        إرسال مهمة إعادة حساب قيمة المحفظة لـ Celery Worker.
        """
        task = recalculate_portfolio_total_value_task.delay(portfolio_id=portfolio_id)
        return {"status": "processing", "task_id": task.id}

    @staticmethod
    def update_market_price_for_symbol(symbol: str, new_price: Decimal):
        """
        تحديث سعر سهم/أصل في السوق وتعديل جميع المحافظ المرتبطة به غير متزامناً.
        """
        task = update_position_market_prices_task.delay(
            symbol=symbol,
            new_price_str=str(new_price)
        )
        return {"status": "price_update_queued", "task_id": task.id}

    @staticmethod
    def record_daily_performance(portfolio_id: int, record_date: date = None):
        """
        جدولة مهمة تسجيل أداء الـ NAV اليومي للمحفظة.
        """
        if record_date is None:
            record_date = date.today()

        task = record_daily_portfolio_performance_task.delay(
            portfolio_id=portfolio_id,
            date_str=record_date.isoformat()
        )
        return {"status": "performance_record_queued", "task_id": task.id}

    @staticmethod
    def check_portfolio_rebalance(portfolio_id: int):
        """
        فحص انحراف الاستراتيجية وإعادة التوازن عبر Celery.
        """
        task = check_rebalancing_needed_task.delay(portfolio_id=portfolio_id)
        return {"status": "rebalance_check_queued", "task_id": task.id}

    @staticmethod
    def get_portfolio_dashboard(portfolio_id: int):
        """
        استرجاع تفاصيل المحفظة وأدائها فورياً وسريعاً من Redis Cache.
        """
        portfolio_data = PortfolioManagementCacheService.get_portfolio_cache(portfolio_id)
        positions = PortfolioManagementCacheService.get_portfolio_positions_cache(portfolio_id)
        performance = PortfolioManagementCacheService.get_portfolio_performance_cache(portfolio_id)
        rebalance_status = PortfolioManagementCacheService.get_rebalance_status_cache(portfolio_id)

        return {
            "portfolio": portfolio_data,
            "positions": positions,
            "performance_history": performance,
            "rebalance_status": rebalance_status,
        }

    #the operations logic on the models 
from decimal import Decimal
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    AssetAllocation,
    Portfolio,
    PortfolioPosition,
    PortfolioPerformance,
)
from .schemas import (
    AssetAllocationCreateSchema,
    AssetAllocationUpdateSchema,
    PortfolioCreateSchema,
    PortfolioUpdateSchema,
    PortfolioPositionCreateSchema,
    PortfolioPositionUpdateSchema,
    PortfolioPerformanceCreateSchema,
    PortfolioPerformanceUpdateSchema,
)

User = get_user_model()


class PortfolioManagementService:

    @classmethod
    @transaction.atomic
    def create_asset_allocation(cls, data: AssetAllocationCreateSchema) -> AssetAllocation:
        total_pct = data.target_stocks_pct + data.target_bonds_pct + data.target_cash_pct
        if total_pct != Decimal("100.00"):
            raise ValidationError(f"Target allocations must sum to 100%. Current sum: {total_pct}%")

        return AssetAllocation.objects.create(
            name=data.name,
            target_stocks_pct=data.target_stocks_pct,
            target_bonds_pct=data.target_bonds_pct,
            target_cash_pct=data.target_cash_pct,
        )

    @staticmethod
    def list_asset_allocations() -> List[AssetAllocation]:
        return AssetAllocation.objects.all()

    @classmethod
    @transaction.atomic
    def update_asset_allocation(cls, allocation_id: int, data: AssetAllocationUpdateSchema) -> AssetAllocation:
        allocation = get_object_or_404(AssetAllocation, id=allocation_id)
        update_data = data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(allocation, key, value)

        total_pct = allocation.target_stocks_pct + allocation.target_bonds_pct + allocation.target_cash_pct
        if total_pct != Decimal("100.00"):
            raise ValidationError(f"Target allocations must sum to 100%. Current sum: {total_pct}%")

        allocation.save()
        return allocation

    @classmethod
    @transaction.atomic
    def create_portfolio(cls, user: User, data: PortfolioCreateSchema) -> Portfolio:
        if Portfolio.objects.filter(account_number=data.account_number).exists():
            raise ValidationError(f"Portfolio with account number '{data.account_number}' already exists.")

        strategy = get_object_or_404(AssetAllocation, id=data.strategy_id) if data.strategy_id else None

        return Portfolio.objects.create(
            user=user,
            strategy=strategy,
            account_number=data.account_number,
            name=data.name,
            status=data.status or "ACTIVE",
            cash_balance=data.cash_balance,
            total_value=data.total_value,
        )

    @staticmethod
    def list_portfolios(user_id: Optional[int] = None, status: Optional[str] = None) -> List[Portfolio]:
        qs = Portfolio.objects.select_related("user", "strategy").all()
        if user_id:
            qs = qs.filter(user_id=user_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    @classmethod
    @transaction.atomic
    def update_portfolio(cls, portfolio_id: int, data: PortfolioUpdateSchema) -> Portfolio:
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        update_data = data.dict(exclude_unset=True)

        if "strategy_id" in update_data:
            strat_id = update_data.pop("strategy_id")
            portfolio.strategy = get_object_or_404(AssetAllocation, id=strat_id) if strat_id else None

        for key, value in update_data.items():
            setattr(portfolio, key, value)

        portfolio.save()
        return portfolio

    @classmethod
    @transaction.atomic
    def create_position(cls, data: PortfolioPositionCreateSchema) -> PortfolioPosition:
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)

        position, _ = PortfolioPosition.objects.update_or_create(
            portfolio=portfolio,
            symbol=data.symbol.upper(),
            defaults={
                "quantity": data.quantity,
                "average_buy_price": data.average_buy_price,
                "current_price": data.current_price,
            },
        )
        cls.recalculate_portfolio_valuation(portfolio)
        return position

    @staticmethod
    def list_positions(portfolio_id: Optional[int] = None, symbol: Optional[str] = None) -> List[PortfolioPosition]:
        qs = PortfolioPosition.objects.select_related("portfolio").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        if symbol:
            qs = qs.filter(symbol__iexact=symbol)
        return qs

    @classmethod
    @transaction.atomic
    def update_position(cls, position_id: int, data: PortfolioPositionUpdateSchema) -> PortfolioPosition:
        position = get_object_or_404(PortfolioPosition, id=position_id)
        update_data = data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(position, key, value)
        position.save()

        cls.recalculate_portfolio_valuation(position.portfolio)
        return position

    @staticmethod
    def recalculate_portfolio_valuation(portfolio: Portfolio):
        positions = portfolio.positions.all()
        holdings_value = sum((pos.quantity * pos.current_price for pos in positions), Decimal("0.0000"))
        portfolio.total_value = portfolio.cash_balance + holdings_value
        portfolio.save(update_fields=["total_value", "updated_at"])

    @classmethod
    @transaction.atomic
    def record_performance(cls, data: PortfolioPerformanceCreateSchema) -> PortfolioPerformance:
        portfolio = get_object_or_404(Portfolio, id=data.portfolio_id)

        perf, _ = PortfolioPerformance.objects.update_or_create(
            portfolio=portfolio,
            date=data.date,
            defaults={
                "nav_value": data.nav_value,
                "daily_return_pct": data.daily_return_pct,
            },
        )
        return perf

    @staticmethod
    def list_performance_records(portfolio_id: Optional[int] = None) -> List[PortfolioPerformance]:
        qs = PortfolioPerformance.objects.select_related("portfolio").all()
        if portfolio_id:
            qs = qs.filter(portfolio_id=portfolio_id)
        return qs
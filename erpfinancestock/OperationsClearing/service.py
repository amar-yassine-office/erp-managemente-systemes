from datetime import date
from typing import Dict, Any

# استيراد المهام مباشرة من tasks.py
from .tasks import (
    process_trade_settlement_execution_task,
    evaluate_margin_requirements_task,
    reconcile_eod_settlements_task,
)
from .cache import OperationsClearingCacheService


class OperationsClearingService:
    """
    طبقة الخدمات (Service Layer) الخاصة بقسم المقاصة والتصفية.
    تستدعي مهام Celery غير المتزامنة وتقرأ من Redis Cache مباشرة.
    """

    @staticmethod
    def execute_settlement(settlement_id: int):
        """
        جدولة مهمة تنفيذ تسوية صفقة مالية عبر Celery.
        """
        task = process_trade_settlement_execution_task.delay(settlement_id=settlement_id)
        return {"status": "settlement_processing", "task_id": task.id}

    @staticmethod
    def evaluate_account_margin(clearing_account_id: int):
        """
        جدولة مهمة فحص حساب الهامش ونداءات الهامش.
        """
        task = evaluate_margin_requirements_task.delay(clearing_account_id=clearing_account_id)
        return {"status": "margin_eval_queued", "task_id": task.id}

    @staticmethod
    def run_eod_reconciliation(clearing_house_id: int, settlement_date: date = None):
        """
        تشغيل مطابقة نهاية اليوم لغرفة مقاصة معينة.
        """
        if settlement_date is None:
            settlement_date = date.today()

        task = reconcile_eod_settlements_task.delay(
            clearing_house_id=clearing_house_id,
            settlement_date_str=settlement_date.isoformat()
        )
        return {"status": "reconciliation_queued", "task_id": task.id}

    @staticmethod
    def get_clearing_operations_dashboard(clearing_account_id: int):
        """
        استرجاع لوحة تحكم عمليات المقاصة، الحسابات الهامشية، وفروقات التسوية من الكاش.
        """
        account_info = OperationsClearingCacheService.get_clearing_account_cache(clearing_account_id)
        margin_data = OperationsClearingCacheService.get_margin_requirement_cache(clearing_account_id)
        open_breaks = OperationsClearingCacheService.get_open_reconciliations_cache(clearing_account_id)

        return {
            "account_info": account_info,
            "margin_status": margin_data,
            "open_reconciliations": open_breaks,
        }

    #the operations on the modles 

    from datetime import datetime, timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    ClearingHouse,
    ClearingMemberAccount,
    TradeSettlement,
    MarginRequirement,
    SettlementReconciliation,
)
from .schemas import (
    ClearingHouseCreateSchema,
    ClearingHouseUpdateSchema,
    ClearingMemberAccountCreateSchema,
    ClearingMemberAccountUpdateSchema,
    TradeSettlementCreateSchema,
    TradeSettlementUpdateSchema,
    MarginRequirementCreateSchema,
    MarginRequirementUpdateSchema,
    SettlementReconciliationCreateSchema,
    SettlementReconciliationUpdateSchema,
)


class OperationsClearingService:

    # =====================================================================
    # 1. CLEARING HOUSE SERVICES
    # =====================================================================

    @staticmethod
    @transaction.atomic
    def create_clearing_house(data: ClearingHouseCreateSchema) -> ClearingHouse:
        if ClearingHouse.objects.filter(code=data.code).exists():
            raise ValidationError(f"A clearing house with code '{data.code}' already exists.")
        
        clearing_house = ClearingHouse.objects.create(
            name=data.name,
            code=data.code,
            country=data.country,
            is_active=data.is_active,
        )
        return clearing_house

    @staticmethod
    def list_clearing_houses(is_active: bool = None):
        queryset = ClearingHouse.objects.all()
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        return queryset

    @staticmethod
    @transaction.atomic
    def update_clearing_house(house_id: int, data: ClearingHouseUpdateSchema) -> ClearingHouse:
        clearing_house = get_object_or_404(ClearingHouse, id=house_id)
        
        for attr, value in data.dict(exclude_unset=True).items():
            setattr(clearing_house, attr, value)
        
        clearing_house.save()
        return clearing_house

    # =====================================================================
    # 2. CLEARING MEMBER ACCOUNT SERVICES
    # =====================================================================

    @staticmethod
    @transaction.atomic
    def create_member_account(data: ClearingMemberAccountCreateSchema) -> ClearingMemberAccount:
        clearing_house = get_object_or_404(ClearingHouse, id=data.clearing_house_id)
        
        if ClearingMemberAccount.objects.filter(account_number=data.account_number).exists():
            raise ValidationError(f"Account number '{data.account_number}' is already registered.")

        account = ClearingMemberAccount.objects.create(
            clearing_house=clearing_house,
            account_number=data.account_number,
            account_name=data.account_name,
            balance=data.balance,
            currency=data.currency,
            is_active=data.is_active,
        )
        return account

    @staticmethod
    def list_member_accounts(clearing_house_id: int = None, is_active: bool = None):
        queryset = ClearingMemberAccount.objects.select_related("clearing_house")
        if clearing_house_id:
            queryset = queryset.filter(clearing_house_id=clearing_house_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        return queryset

    @staticmethod
    @transaction.atomic
    def update_member_account(account_id: int, data: ClearingMemberAccountUpdateSchema) -> ClearingMemberAccount:
        account = get_object_or_404(ClearingMemberAccount, id=account_id)

        for attr, value in data.dict(exclude_unset=True).items():
            setattr(account, attr, value)

        account.save()
        return account

    # =====================================================================
    # 3. TRADE SETTLEMENT SERVICES
    # =====================================================================

    @staticmethod
    @transaction.atomic
    def create_trade_settlement(staff_user, data: TradeSettlementCreateSchema) -> TradeSettlement:
        clearing_house = get_object_or_404(ClearingHouse, id=data.clearing_house_id)
        clearing_account = get_object_or_404(ClearingMemberAccount, id=data.clearing_account_id)

        if TradeSettlement.objects.filter(trade_id=data.trade_id).exists():
            raise ValidationError(f"Trade settlement record for Trade ID '{data.trade_id}' already exists.")

        settlement = TradeSettlement.objects.create(
            trade_id=data.trade_id,
            clearing_house=clearing_house,
            clearing_account=clearing_account,
            user=staff_user,
            symbol=data.symbol,
            quantity=data.quantity,
            price=data.price,
            total_amount=data.total_amount,
            settlement_type=data.settlement_type,
            status=data.status,
            trade_date=data.trade_date,
            settlement_date=data.settlement_date,
            actual_settlement_time=data.actual_settlement_time,
        )
        return settlement

    @staticmethod
    def list_trade_settlements(status: str = None, settlement_type: str = None, symbol: str = None):
        queryset = TradeSettlement.objects.select_related("clearing_house", "clearing_account", "user")
        if status:
            queryset = queryset.filter(status=status)
        if settlement_type:
            queryset = queryset.filter(settlement_type=settlement_type)
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        return queryset

    @staticmethod
    @transaction.atomic
    def update_trade_settlement(settlement_id: int, data: TradeSettlementUpdateSchema) -> TradeSettlement:
        settlement = get_object_or_404(TradeSettlement, id=settlement_id)

        update_data = data.dict(exclude_unset=True)
        
        # If status changes to SETTLED and time wasn't explicitly given, timestamp it now
        if update_data.get("status") == "SETTLED" and not update_data.get("actual_settlement_time"):
            if not settlement.actual_settlement_time:
                settlement.actual_settlement_time = datetime.now(timezone.utc)

        for attr, value in update_data.items():
            setattr(settlement, attr, value)

        settlement.save()
        return settlement

    # =====================================================================
    # 4. MARGIN REQUIREMENT SERVICES
    # =====================================================================

    @staticmethod
    @transaction.atomic
    def create_margin_requirement(data: MarginRequirementCreateSchema) -> MarginRequirement:
        account = get_object_or_404(ClearingMemberAccount, id=data.clearing_account_id)

        margin = MarginRequirement.objects.create(
            clearing_account=account,
            initial_margin=data.initial_margin,
            maintenance_margin=data.maintenance_margin,
            collateral_posted=data.collateral_posted,
            margin_call_amount=data.margin_call_amount,
            is_margin_call_active=data.is_margin_call_active,
        )
        return margin

    @staticmethod
    def list_margin_requirements(is_margin_call_active: bool = None):
        queryset = MarginRequirement.objects.select_related("clearing_account")
        if is_margin_call_active is not None:
            queryset = queryset.filter(is_margin_call_active=is_margin_call_active)
        return queryset

    @staticmethod
    @transaction.atomic
    def update_margin_requirement(margin_id: int, data: MarginRequirementUpdateSchema) -> MarginRequirement:
        margin = get_object_or_404(MarginRequirement, id=margin_id)

        for attr, value in data.dict(exclude_unset=True).items():
            setattr(margin, attr, value)

        # Automatic check: if collateral falls below maintenance margin, activate margin call
        if margin.collateral_posted < margin.maintenance_margin:
            margin.is_margin_call_active = True
            margin.margin_call_amount = margin.initial_margin - margin.collateral_posted
        elif margin.collateral_posted >= margin.initial_margin:
            margin.is_margin_call_active = False
            margin.margin_call_amount = 0.0000

        margin.save()
        return margin

    # =====================================================================
    # 5. SETTLEMENT RECONCILIATION SERVICES
    # =====================================================================

    @staticmethod
    @transaction.atomic
    def create_reconciliation_break(data: SettlementReconciliationCreateSchema) -> SettlementReconciliation:
        settlement = get_object_or_404(TradeSettlement, id=data.settlement_id)

        break_record = SettlementReconciliation.objects.create(
            settlement=settlement,
            break_type=data.break_type,
            description=data.description,
            status=data.status if data.status else "OPEN",
        )
        return break_record

    @staticmethod
    def list_reconciliation_breaks(status: str = None, break_type: str = None):
        queryset = SettlementReconciliation.objects.select_related("settlement", "resolved_by")
        if status:
            queryset = queryset.filter(status=status)
        if break_type:
            queryset = queryset.filter(break_type=break_type)
        return queryset

    @staticmethod
    @transaction.atomic
    def update_reconciliation_break(break_id: int, staff_user, data: SettlementReconciliationUpdateSchema) -> SettlementReconciliation:
        break_record = get_object_or_404(SettlementReconciliation, id=break_id)

        update_data = data.dict(exclude_unset=True)

        if update_data.get("status") == "RESOLVED" and break_record.status != "RESOLVED":
            break_record.resolved_by = staff_user
            break_record.resolved_at = datetime.now(timezone.utc)

        for attr, value in update_data.items():
            setattr(break_record, attr, value)

        break_record.save()
        return break_record
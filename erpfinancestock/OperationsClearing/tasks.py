from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from .models import (
    ClearingHouse,
    ClearingMemberAccount,
    TradeSettlement,
    MarginRequirement,
    SettlementReconciliation,
)
from .cache import OperationsClearingCacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_trade_settlement_execution_task(self, settlement_id: int):
    """
    مهمة غير متزامنة لتنفيذ عملية تسوية الصفقة (DVP/RVP)، تحديث رصيد الحساب،
    وتسجيل وقت التسوية الفعلي.
    """
    try:
        with transaction.atomic():
            settlement = TradeSettlement.objects.select_for_update().get(id=settlement_id)

            if settlement.status != 'PENDING':
                return f"Settlement {settlement_id} is already processed ({settlement.status})."

            clearing_account = ClearingMemberAccount.objects.select_for_update().get(
                id=settlement.clearing_account_id
            )

            # خصم أو إيداع المبالغ بناءً على طبيعة العملية (DVP/RVP)
            if settlement.settlement_type in ['DVP', 'FOP']:
                clearing_account.balance -= settlement.total_amount
            elif settlement.settlement_type == 'RVP':
                clearing_account.balance += settlement.total_amount

            clearing_account.save(update_fields=['balance'])

            # تحديث حالة التسوية
            settlement.status = 'SETTLED'
            settlement.actual_settlement_time = timezone.now()
            settlement.save(update_fields=['status', 'actual_settlement_time', 'updated_at'])

        # إبطال الكاش الخاص بالحساب والتسويات
        OperationsClearingCacheService.invalidate_clearing_account_cache(clearing_account.id)
        OperationsClearingCacheService.invalidate_trade_settlement_cache(settlement_id)

        logger.info(f"Trade Settlement #{settlement.trade_id} successfully executed.")
        return f"Settlement #{settlement.trade_id} completed successfully."

    except TradeSettlement.DoesNotExist:
        logger.error(f"TradeSettlement ID {settlement_id} not found.")
        return None
    except Exception as exc:
        logger.error(f"Error executing settlement {settlement_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def evaluate_margin_requirements_task(self, clearing_account_id: int):
    """
    مهمة فحص متطلبات الهامش (Margin Requirements) وإصدار نداء الهامش (Margin Call)
    إذا انخفضت الضمانات المودعة عن هامش الصيانة المطلوب.
    """
    try:
        margin_req = MarginRequirement.objects.get(clearing_account_id=clearing_account_id)

        # إذا كانت الضمانات أقل من هامش الصيانة المطلوب
        if margin_req.collateral_posted < margin_req.maintenance_margin:
            shortfall = margin_req.initial_margin - margin_req.collateral_posted
            margin_req.margin_call_amount = max(shortfall, Decimal('0.0000'))
            margin_req.is_margin_call_active = True
            logger.warning(f"MARGIN CALL TRIGGERED for Account {clearing_account_id}: Amount {margin_req.margin_call_amount}")
        else:
            margin_req.margin_call_amount = Decimal('0.0000')
            margin_req.is_margin_call_active = False

        margin_req.save(update_fields=['margin_call_amount', 'is_margin_call_active', 'last_updated'])

        # تحديث كاش الهامش الخاص بالحساب
        OperationsClearingCacheService.invalidate_margin_requirement_cache(clearing_account_id)

        return f"Margin evaluation complete for account {clearing_account_id}. Active Call: {margin_req.is_margin_call_active}"

    except MarginRequirement.DoesNotExist:
        logger.error(f"MarginRequirement record not found for Clearing Account {clearing_account_id}")
        return None


@shared_task
def reconcile_eod_settlements_task(clearing_house_id: int, settlement_date_str: str):
    """
    مهمة مطابقة نهاية اليوم (End of Day Reconciliation) لتسويات غرفة المقاصة
    والكشف عن أي فروقات أو صفقات مفقودة وتوليد سجلات SettlementReconciliation.
    """
    pending_settlements = TradeSettlement.objects.filter(
        clearing_house_id=clearing_house_id,
        settlement_date=settlement_date_str,
        status='PENDING'
    )

    breaks_created = 0
    for settlement in pending_settlements:
        # تسجيل فارق في حال عدم اكتمال التسوية بحلول نهاية يوم التسوية
        if settlement.settlement_date < timezone.now().date():
            settlement.status = 'FAILED'
            settlement.save(update_fields=['status', 'updated_at'])

            SettlementReconciliation.objects.create(
                settlement=settlement,
                break_type='MISSING_CLEARING',
                description=f"Automated EOD Break: Settlement failed to settle on date {settlement_date_str}.",
                status='OPEN'
            )
            breaks_created += 1

    OperationsClearingCacheService.invalidate_reconciliation_cache(clearing_house_id)
    return f"EOD Reconciliation finished for Clearing House {clearing_house_id}: {breaks_created} breaks generated."
from typing import Dict, Any, Optional
from .tasks import (
    create_audit_log_async_task,
    run_automated_trade_surveillance_task,
    notify_compliance_officers_on_critical_sar_task,
)


class ComplianceLegalService:

    @staticmethod
    def log_audit_event_async(actor_id: Optional[int], action_type: str, target_model: str, target_id: Any, ip_address: str = None, changes: dict = None):
        """
        خدمة مخصصة لإرسال سجلات الـ Audit Log إلى Celery مباشرة.
        """
        create_audit_log_async_task.delay(
            actor_id=actor_id,
            action_type=action_type,
            target_model=target_model,
            target_id=str(target_id),
            ip_address=ip_address or "0.0.0.0",
            changes=changes or {}
        )

    @staticmethod
    def inspect_trade_surveillance_async(user_id: int, symbol: str, order_volume: float, trade_price: float):
        """
        خدمة مراقبة التداولات بعد التنفيذ.
        """
        run_automated_trade_surveillance_task.delay(user_id, symbol, order_volume, trade_price)

    @staticmethod
    def trigger_sar_notification(sar_id: int):
        """
        إرسال تنبيهات للـ SARs عالية الخطورة.
        """
        notify_compliance_officers_on_critical_sar_task.delay(sar_id)

        #THE LOGIC OF THE OPERETAIONS ON THE MODELS  

        from typing import List, Optional, Dict, Any
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import (
    ComplianceCheck,
    RestrictedAsset,
    SuspiciousActivityReport,
    TradeSurveillanceRule,
    AuditLog,
)
from .schemas import (
    ComplianceCheckCreateSchema,
    ComplianceCheckUpdateSchema,
    RestrictedAssetCreateSchema,
    RestrictedAssetUpdateSchema,
    SuspiciousActivityReportCreateSchema,
    SuspiciousActivityReportUpdateSchema,
    TradeSurveillanceRuleCreateSchema,
    TradeSurveillanceRuleUpdateSchema,
)

User = get_user_model()


class ComplianceLegalService:

    @classmethod
    @transaction.atomic
    def create_compliance_check(cls, staff_user: User, data: ComplianceCheckCreateSchema) -> ComplianceCheck:
        target_user = get_object_or_404(User, id=data.user_id)
        check = ComplianceCheck.objects.create(
            user=target_user,
            check_type=data.check_type,
            status=data.status,
            notes=data.notes or "",
            performed_by=staff_user,
            next_review_date=data.next_review_date,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="ComplianceCheck", target_id=str(check.id))
        return check

    @classmethod
    @transaction.atomic
    def update_compliance_check(cls, check_id: int, staff_user: User, data: ComplianceCheckUpdateSchema) -> ComplianceCheck:
        check = get_object_or_404(ComplianceCheck, id=check_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(check, key, value)
        check.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="ComplianceCheck", target_id=str(check.id), changes=update_data)
        return check

    @staticmethod
    def list_compliance_checks(user_id: Optional[int] = None, check_type: Optional[str] = None, status: Optional[str] = None) -> List[ComplianceCheck]:
        qs = ComplianceCheck.objects.select_related("user", "performed_by").all()
        if user_id:
            qs = qs.filter(user_id=user_id)
        if check_type:
            qs = qs.filter(check_type=check_type)
        if status:
            qs = qs.filter(status=status)
        return qs

    @classmethod
    @transaction.atomic
    def add_restricted_asset(cls, staff_user: User, data: RestrictedAssetCreateSchema) -> RestrictedAsset:
        asset = RestrictedAsset.objects.create(
            symbol=data.symbol.upper(),
            company_name=data.company_name,
            reason=data.reason,
            description=data.description or "",
            is_active=data.is_active,
            start_date=data.start_date,
            end_date=data.end_date,
            added_by=staff_user,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="RestrictedAsset", target_id=str(asset.id))
        return asset

    @classmethod
    @transaction.atomic
    def update_restricted_asset(cls, asset_id: int, staff_user: User, data: RestrictedAssetUpdateSchema) -> RestrictedAsset:
        asset = get_object_or_404(RestrictedAsset, id=asset_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)
        asset.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="RestrictedAsset", target_id=str(asset.id), changes=update_data)
        return asset

    @staticmethod
    def list_restricted_assets(is_active_only: bool = True) -> List[RestrictedAsset]:
        qs = RestrictedAsset.objects.select_related("added_by").all()
        if is_active_only:
            qs = qs.filter(is_active=True)
        return qs

    @classmethod
    @transaction.atomic
    def raise_sar(cls, staff_user: User, data: SuspiciousActivityReportCreateSchema) -> SuspiciousActivityReport:
        target_user = get_object_or_404(User, id=data.user_id)
        report = SuspiciousActivityReport.objects.create(
            user=target_user,
            portfolio_account_number=data.portfolio_account_number or "",
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=data.status,
            investigated_by=staff_user,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="SuspiciousActivityReport", target_id=str(report.id))
        return report

    @classmethod
    @transaction.atomic
    def update_sar_status(cls, report_id: int, staff_user: User, data: SuspiciousActivityReportUpdateSchema) -> SuspiciousActivityReport:
        report = get_object_or_404(SuspiciousActivityReport, id=report_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(report, key, value)
        report.investigated_by = staff_user
        report.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="SuspiciousActivityReport", target_id=str(report.id), changes=update_data)
        return report

    @staticmethod
    def list_sars(severity: Optional[str] = None, status: Optional[str] = None) -> List[SuspiciousActivityReport]:
        qs = SuspiciousActivityReport.objects.select_related("user", "investigated_by").all()
        if severity:
            qs = qs.filter(severity=severity)
        if status:
            qs = qs.filter(status=status)
        return qs

    @classmethod
    @transaction.atomic
    def create_surveillance_rule(cls, staff_user: User, data: TradeSurveillanceRuleCreateSchema) -> TradeSurveillanceRule:
        rule = TradeSurveillanceRule.objects.create(
            rule_name=data.rule_name,
            rule_type=data.rule_type,
            description=data.description,
            threshold_value=data.threshold_value,
            is_active=data.is_active,
        )
        cls.log_audit_event(actor=staff_user, action_type="CREATE", target_model="TradeSurveillanceRule", target_id=str(rule.id))
        return rule

    @classmethod
    @transaction.atomic
    def update_surveillance_rule(cls, rule_id: int, staff_user: User, data: TradeSurveillanceRuleUpdateSchema) -> TradeSurveillanceRule:
        rule = get_object_or_404(TradeSurveillanceRule, id=rule_id)
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key == "threshold_value" and value is not None:
                value = Decimal(str(value))
            setattr(rule, key, value)
        rule.save()
        cls.log_audit_event(actor=staff_user, action_type="UPDATE", target_model="TradeSurveillanceRule", target_id=str(rule.id), changes=update_data)
        return rule

    @staticmethod
    def log_audit_event(actor: Optional[User], action_type: str, target_model: str, target_id: str = "", changes: Optional[Dict[str, Any]] = None) -> AuditLog:
        return AuditLog.objects.create(
            actor=actor if actor and actor.is_authenticated else None,
            action_type=action_type,
            target_model=target_model,
            target_id=target_id,
            changes=changes or {},
        )

    @staticmethod
    def list_audit_logs(actor_id: Optional[int] = None, action_type: Optional[str] = None) -> List[AuditLog]:
        qs = AuditLog.objects.select_related("actor").all()
        if actor_id:
            qs = qs.filter(actor_id=actor_id)
        if action_type:
            qs = qs.filter(action_type=action_type)
        return qs
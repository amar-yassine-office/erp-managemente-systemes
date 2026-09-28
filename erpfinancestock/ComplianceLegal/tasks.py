from datetime import date
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

from .models import (
    ComplianceCheck,
    RestrictedAsset,
    SuspiciousActivityReport,
    TradeSurveillanceRule,
    AuditLog,
)


@shared_task
def create_audit_log_async_task(actor_id: int, action_type: str, target_model: str, target_id: str, ip_address: str, changes: dict):
    """
    تسجيل عمليات التعديل والوصول (Audit Trail) بشكل غير متزامن لمنع إبطاء زمن استجابة الـ APIs.
    """
    AuditLog.objects.create(
        actor_id=actor_id,
        action_type=action_type,
        target_model=target_model,
        target_id=str(target_id),
        ip_address=ip_address,
        changes=changes or {}
    )
    return f"Audit log created for {target_model} #{target_id} by User #{actor_id}."


@shared_task
def run_automated_trade_surveillance_task(user_id: int, symbol: str, order_volume: float, trade_price: float):
    """
    فحص التداول المُنَفَّذ مقابل قواعد المراقبة (Spoofing, Wash Trading, Large Orders) وإنشاء SAR تلقائياً إذا تجاوَز العتبة.
    """
    active_rules = TradeSurveillanceRule.objects.filter(is_active=True)
    flagged_rules = []

    for rule in active_rules:
        # مثال: فحص أحجام الأوامر الشاذة
        if rule.rule_type == 'LARGE_ORDER' and order_volume >= float(rule.threshold_value):
            flagged_rules.append(rule)

    if flagged_rules:
        rule_names = ", ".join([r.rule_name for r in flagged_rules])
        sar = SuspiciousActivityReport.objects.create(
            user_id=user_id,
            title=f"Automated Surveillance Alert: {symbol}",
            description=f"Automated check triggered for symbol {symbol}. Volume: {order_volume}. Rules matched: {rule_names}",
            severity='HIGH',
            status='UNDER_REVIEW'
        )
        return f"Suspicious Activity Report #{sar.id} created for User #{user_id}."

    return f"Surveillance check passed for User #{user_id} on {symbol}."


@shared_task
def check_due_compliance_reviews_task():
    """
    مهمة دورية (Periodic Task) لتحديث مراجعات KYC/AML التي حان موعد مراجعتها الدوري إلى EXPIRED.
    """
    today = date.today()
    due_checks = ComplianceCheck.objects.filter(
        status='PASSED',
        next_review_date__lte=today
    )
    
    updated_count = due_checks.update(status='EXPIRED')
    return f"Compliance review check completed: {updated_count} checks marked as EXPIRED."


@shared_task
def notify_compliance_officers_on_critical_sar_task(sar_id: int):
    """
    إرسال إشعار فوري لمسؤولي الامتثال والرقابة القانونية عند فتح تقرير نشاط مشبوه عالي الخطورة.
    """
    try:
        sar = SuspiciousActivityReport.objects.select_related('user').get(id=sar_id)
        if sar.severity in ['HIGH', 'CRITICAL']:
            subject = f"[URGENT] High Severity SAR Created #{sar.id} - User: {sar.user.username}"
            message = (
                f"A new suspicious activity report requires immediate review.\n\n"
                f"Title: {sar.title}\n"
                f"Severity: {sar.get_severity_display()}\n"
                f"Description: {sar.description}\n"
            )
            # إرسال إلى بريد فريق الامتثال
            compliance_email = getattr(settings, 'COMPLIANCE_OFFICER_EMAIL', settings.DEFAULT_FROM_EMAIL)
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [compliance_email],
                fail_silently=True
            )
            return f"Notification sent for SAR #{sar_id}."
    except SuspiciousActivityReport.DoesNotExist:
        return f"SAR #{sar_id} not found."
from datetime import date
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import KYCDocument, ClientProfile, LeadPipeline, InteractionLog


@shared_task
def process_kyc_verification_task(kyc_document_id: int, approved: bool, rejection_reason: str = ""):
    """
    معالجة حالة توثيق مستند KYC وإرسال إشعار للعميل بالنتيجة.
    """
    try:
        doc = KYCDocument.objects.select_related('client__user').get(id=kyc_document_id)
        
        if approved:
            doc.status = 'APPROVED'
            doc.verified_at = timezone.now()
            doc.rejection_reason = ""
        else:
            doc.status = 'REJECTED'
            doc.rejection_reason = rejection_reason

        doc.save(update_fields=['status', 'verified_at', 'rejection_reason'])

        # إرسال بريد إلكتروني تلقائي للعميل بنتيجة التوثيق
        user_email = doc.client.user.email
        if user_email:
            subject = f"تحديث حالة توثيق المستندات - {doc.get_document_type_display()}"
            message = (
                f"عزيزي العميل، تم قبول مستندك بنجاح."
                if approved else
                f"عزيزي العميل، تم رفض المستند بسبب: {rejection_reason}"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                fail_silently=True
            )

        return f"KYC Document #{kyc_document_id} updated to {doc.status}."

    except KYCDocument.DoesNotExist:
        return f"KYC Document ID {kyc_document_id} not found."


@shared_task
def check_expired_kyc_documents_task():
    """
    مهمة دورية (Periodic Task) تفحص المستندات المنتهية الصلاحية وتحدث حالتها إلى EXPIRED.
    """
    today = date.today()
    expired_docs = KYCDocument.objects.filter(
        status='APPROVED',
        expiry_date__lt=today
    )
    
    count = expired_docs.update(status='EXPIRED')
    return f"Checked KYC expiry: {count} documents updated to EXPIRED."


@shared_task
def convert_lead_to_client_profile_task(lead_id: int, user_id: int, relationship_manager_id: int = None):
    """
    تحويل فرصة بيعية (Lead) كسبت إلى بروفايل عميل رسمي (ClientProfile) في النظام.
    """
    with transaction.atomic():
        try:
            lead = LeadPipeline.objects.select_for_update().get(id=lead_id)
            
            # التأكد من تحديث مرحلة الـ Lead إلى WON
            lead.stage = 'WON'
            lead.save(update_fields=['stage'])

            # إنشاء بروفايل العميل
            profile, created = ClientProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'client_type': 'INDIVIDUAL',
                    'net_worth_estimate': lead.estimated_investment_amount,
                    'relationship_manager_id': relationship_manager_id or lead.assigned_to_id,
                }
            )

            return f"Lead #{lead_id} successfully converted to ClientProfile #{profile.id}."

        except LeadPipeline.DoesNotExist:
            return f"Lead ID {lead_id} not found."


@shared_task
def send_interaction_followup_reminder_task():
    """
    مهمة تذكير لمديري العلاقات بالمتابعات المطلوبة لهذا اليوم بناءً على سجلات التفاعل.
    """
    today = date.today()
    pending_followups = InteractionLog.objects.filter(
        follow_up_required=True,
        follow_up_date=today
    ).select_related('staff_member', 'client__user')

    reminders_sent = 0
    for log in pending_followups:
        if log.staff_member and log.staff_member.email:
            send_mail(
                subject=f"تذكير بمتابعة عميل: {log.client.user.get_full_name()}",
                message=f"لديك موعد متابعة اليوم للعميل {log.client.user.get_full_name()}.\nالموضوع: {log.subject}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[log.staff_member.email],
                fail_silently=True
            )
            reminders_sent += 1

    return f"Sent {reminders_sent} follow-up reminders to staff members."
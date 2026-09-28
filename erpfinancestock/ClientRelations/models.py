from django.db import models

# Create your models here.
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class ClientProfile(models.Model):
    """Extended CRM profile for individual and institutional clients."""

    CLIENT_TYPES = (
        ('INDIVIDUAL', 'Individual Investor'),
        ('CORPORATE', 'Corporate / Institutional'),
        ('FAMILY_OFFICE', 'Family Office'),
    )

    RISK_TOLERANCE_CHOICES = (
        ('CONSERVATIVE', 'Conservative'),
        ('MODERATE', 'Moderate'),
        ('AGGRESSIVE', 'Aggressive'),
    )

    # Linked to Django User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile',
    )

    client_type = models.CharField(
        max_length=20, choices=CLIENT_TYPES, default='INDIVIDUAL'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    # Wealth Management Attributes
    risk_tolerance = models.CharField(
        max_length=20, choices=RISK_TOLERANCE_CHOICES, default='MODERATE'
    )
    net_worth_estimate = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    investment_goal = models.CharField(max_length=255, blank=True)

    # Dedicated Wealth Manager / Relationship Officer
    relationship_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_clients',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_client_type_display()})"


class KYCDocument(models.Model):
    """KYC (Know Your Customer) and AML compliance verification files."""

    DOCUMENT_TYPES = (
        ('PASSPORT', 'Passport'),
        ('NATIONAL_ID', 'National ID'),
        ('UTILITY_BILL', 'Proof of Address (Utility Bill)'),
        ('TAX_CERTIFICATE', 'Tax Certificate'),
        ('CORPORATE_REG', 'Commercial Register / Articles'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    )

    client = models.ForeignKey(
        ClientProfile, on_delete=models.CASCADE, related_name='kyc_documents'
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True)
    file = models.FileField(
        upload_to='kyc_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING'
    )
    rejection_reason = models.TextField(blank=True)

    expiry_date = models.DateField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.client.user.username} - {self.get_document_type_display()} ({self.status})"


class InteractionLog(models.Model):
    """Logs all communications, meetings, calls, and support notes with clients."""

    CHANNEL_CHOICES = (
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Call'),
        ('MEETING', 'In-Person Meeting'),
        ('PORTAL', 'Client Portal Message'),
    )

    client = models.ForeignKey(
        ClientProfile, on_delete=models.CASCADE, related_name='interaction_logs'
    )
    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logged_interactions',
    )

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='EMAIL')
    subject = models.CharField(max_length=255)
    summary = models.TextField()
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.user.username} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


class LeadPipeline(models.Model):
    """Prospect and sales pipeline management for attracting new wealth management clients."""

    STAGE_CHOICES = (
        ('NEW', 'New Lead'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified Prospect'),
        ('PROPOSAL', 'Proposal Sent'),
        ('WON', 'Converted to Client'),
        ('LOST', 'Lost Opportunity'),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    estimated_investment_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='NEW')

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_stage_display()})"
    
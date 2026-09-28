from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class ComplianceCheck(models.Model):
    """Tracks regulatory verification (KYC/AML) and compliance clearance for users."""

    CHECK_TYPES = (
        ('KYC_VERIFICATION', 'Know Your Customer (KYC)'),
        ('AML_SCREENING', 'Anti-Money Laundering (AML)'),
        ('PEP_CHECK', 'Politically Exposed Person (PEP)'),
        ('SANCTION_LIST', 'Sanctions List Screening'),
    )

    STATUS_CHOICES = (
        ('PASSED', 'Passed'),
        ('FLAGGED', 'Flagged / Suspicious'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired / Re-check Required'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='compliance_checks',
    )
    check_type = models.CharField(max_length=30, choices=CHECK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FLAGGED')

    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_compliance_checks',
    )

    checked_at = models.DateTimeField(auto_now_add=True)
    next_review_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_check_type_display()}: {self.status}"


class RestrictedAsset(models.Model):
    """Tracks instruments restricted from trading due to insider info or regulatory bans."""

    RESTRICTION_REASONS = (
        ('INSIDER_INFO', 'Insider Knowledge / Material Non-Public Info'),
        ('REGULATORY_BAN', 'Regulatory Sanction / Ban'),
        ('CONFLICT_OF_INTEREST', 'Corporate Conflict of Interest'),
    )

    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    company_name = models.CharField(max_length=200)
    reason = models.CharField(max_length=30, choices=RESTRICTION_REASONS)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_restricted_assets',
    )

    def __str__(self):
        return f"{self.symbol} ({self.get_reason_display()})"


class SuspiciousActivityReport(models.Model):
    """Logs AML flags, suspicious trading patterns, and legal reports (SAR/STR)."""

    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    STATUS_CHOICES = (
        ('UNDER_REVIEW', 'Under Internal Review'),
        ('REPORTED_TO_AUTHORITIES', 'Reported to Regulatory Authorities'),
        ('DISMISSED', 'Dismissed / False Positive'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suspicious_reports',
    )
    portfolio_account_number = models.CharField(
        max_length=100, blank=True, help_text="Target portfolio account number"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Detailed narrative of suspicious activity")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='UNDER_REVIEW')

    investigated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_sars',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SAR #{self.id} - {self.user.username} [{self.severity}]"


class TradeSurveillanceRule(models.Model):
    """Automated trade surveillance parameters (e.g., Wash Trading, Spoofing, Front Running)."""

    RULE_TYPES = (
        ('WASH_TRADING', 'Wash Trading Detection'),
        ('FRONT_RUNNING', 'Front Running Detection'),
        ('LARGE_ORDER', 'Unusually Large Order Volume'),
        ('PATTERN_DAY_TRADER', 'Pattern Day Trading Limit'),
    )

    rule_name = models.CharField(max_length=150)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    description = models.TextField()
    threshold_value = models.DecimalField(max_digits=18, decimal_places=4)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rule_name} ({self.get_rule_type_display()})"


class AuditLog(models.Model):
    """Immutable audit trail logging actions, modifications, and access events."""

    ACTION_TYPES = (
        ('CREATE', 'Resource Created'),
        ('UPDATE', 'Resource Updated'),
        ('DELETE', 'Resource Deleted'),
        ('TRADE_EXECUTION', 'Trade Order Executed'),
        ('LOGIN_ATTEMPT', 'Security Login Event'),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions',
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    target_model = models.CharField(max_length=100, help_text="Target entity, e.g. Portfolio")
    target_id = models.CharField(max_length=50, blank=True, help_text="Primary key of object")

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes = models.JSONField(default=dict, help_text="JSON payload of modifications")

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.actor} - {self.action_type} on {self.target_model}"
    
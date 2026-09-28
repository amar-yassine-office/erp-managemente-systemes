from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class SystemServer(models.Model):
    """Tracks physical/virtual server infrastructure hosting the ERP services."""

    SERVER_TYPES = (
        ('APP', 'Application Server (Django/Gunicorn)'),
        ('DB', 'Database Server (PostgreSQL)'),
        ('CACHE', 'Cache / Broker (Redis)'),
        ('WORKER', 'Asynchronous Task Worker (Celery)'),
    )

    STATUS_CHOICES = (
        ('ONLINE', 'Online / Healthy'),
        ('DEGRADED', 'Degraded Performance'),
        ('OFFLINE', 'Offline / Critical'),
        ('MAINTENANCE', 'Under Maintenance'),
    )

    name = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    server_type = models.CharField(max_length=20, choices=SERVER_TYPES, default='APP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ONLINE')
    cpu_usage_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    memory_usage_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_ping = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_status_display()}"


class APIKey(models.Model):
    """Manages API keys for external integrations, algorithmic traders, and institutional feeds."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_keys',
    )
    key_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=128, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.key_name} ({self.user.username})"


class AsyncTaskLog(models.Model):
    """Logs Celery background tasks, queue execution statuses, and execution times."""

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('RETRY', 'Retrying'),
    )

    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    task_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    runtime_seconds = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    traceback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_name} [{self.status}]"


class SystemSetting(models.Model):
    """Global system-wide environment configurations and maintenance modes."""

    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(help_text="Configuration value (String, JSON, or Boolean)")
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class SystemIncident(models.Model):
    """Tracks IT system outages, maintenance logs, and infrastructure issues."""

    SEVERITY_CHOICES = (
        ('LOW', 'Minor Degradation'),
        ('MEDIUM', 'Partial Outage'),
        ('HIGH', 'Major Outage'),
        ('CRITICAL', 'Critical System Failure'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('IDENTIFIED', 'Problem Identified'),
        ('RESOLVED', 'Resolved'),
    )

    server = models.ForeignKey(
        SystemServer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='incidents',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title} - {self.status}"
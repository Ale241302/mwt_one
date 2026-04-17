"""
S26: Modelos del sistema de notificaciones email.
C1: NotificationTemplate — templates Jinja2 editables CEO
C2a: NotificationAttempt — append-only, 1..N por evento
C2b: NotificationLog — resultado final consolidado, 0..1 por evento+recipient
C3: CollectionEmailLog — audit trail cobranza automática
ImmutableManager: bloquea QuerySet.update/delete en modelos de audit trail
"""
import uuid
from django.db import models
from django.conf import settings
from apps.core.models import UUIDReferenceField


# =============================================================================
# ImmutableManager — bloquea bulk update/delete en audit trail models
# =============================================================================

class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise PermissionError("Bulk update prohibited on immutable audit trail model.")

    def delete(self):
        raise PermissionError("Bulk delete prohibited on immutable audit trail model.")


class ImmutableManager(models.Manager):
    def get_queryset(self):
        return ImmutableQuerySet(self.model, using=self._db)


# =============================================================================
# C1: NotificationTemplate
# =============================================================================

class NotificationTemplate(models.Model):
    """
    Template Jinja2 editable por CEO.
    Soft delete via is_active=False — no DELETE real.
    UniqueConstraint condicional: brand=null vs brand!=null.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text='Título administrativo: "Registro de expediente"')
    template_key = models.CharField(max_length=50, db_index=True, help_text='Clave de resolución: expediente.registered, etc.')
    subject_template = models.TextField(help_text='Jinja2 — asunto del email')
    body_template = models.TextField(help_text='Jinja2 — cuerpo plain text, no HTML para MVP')
    is_active = models.BooleanField(default=True)
    brand_id = UUIDReferenceField(
        target_module='brands',
        null=True, blank=True,
        help_text='brand=null → default. brand=X → override por marca.'
    )

    @property
    def brand(self):
        return self.resolve_ref('brand_id')
    language = models.CharField(max_length=5, default='es', help_text='ISO 639-1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='created_notification_templates'
    )

    class Meta:
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        constraints = [
            # Fix B1 R2: UniqueConstraint condicional para brand=null.
            # NULL != NULL en PostgreSQL rompe unique_together con brand null.
            models.UniqueConstraint(
                fields=['template_key', 'language'],
                condition=models.Q(brand_id__isnull=True),
                name='uniq_default_template_per_key_lang'
            ),
            models.UniqueConstraint(
                fields=['template_key', 'brand_id', 'language'],
                condition=models.Q(brand_id__isnull=False),
                name='uniq_brand_template_per_key_lang'
            ),
        ]

    def __str__(self):
        brand_str = self.brand.slug if self.brand else 'default'
        return f'{self.template_key} [{self.language}] ({brand_str})'


# =============================================================================
# C2a: NotificationAttempt — append-only
# =============================================================================

class NotificationAttempt(models.Model):
    """
    Registro inmutable de cada intento de envío. Append-only. 1..N por evento.
    Enforcement: delete() y save() sobre existentes lanzan PermissionError.
    ImmutableManager bloquea bulk update/delete.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correlation_id = models.UUIDField(db_index=True, help_text='Agrupa attempts con su log terminal.')
    event_log_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    expediente_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    proforma_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)

    @property
    def event_log(self):
        return self.resolve_ref('event_log_id')

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    @property
    def proforma(self):
        return self.resolve_ref('proforma_id')
    recipient_email = models.EmailField()
    template_key = models.CharField(max_length=50, blank=True, default='')
    trigger_action_source = models.CharField(max_length=32, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped'),
            ('disabled', 'Disabled'),
        ]
    )
    error = models.TextField(blank=True, default='')
    attempted_at = models.DateTimeField(auto_now_add=True)

    objects = ImmutableManager()

    class Meta:
        verbose_name = 'Notification Attempt'
        verbose_name_plural = 'Notification Attempts'
        indexes = [
            models.Index(fields=['event_log', '-attempted_at']),
            models.Index(fields=['correlation_id']),
        ]

    def delete(self, *args, **kwargs):
        raise PermissionError("NotificationAttempt is append-only. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and NotificationAttempt.objects.filter(pk=self.pk).exists():
            raise PermissionError("NotificationAttempt is append-only. Cannot update.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Attempt [{self.status}] {self.template_key} → {self.recipient_email}'


# =============================================================================
# C2b: NotificationLog — resultado final consolidado
# =============================================================================

class NotificationLog(models.Model):
    """
    Registro final único por evento+recipient. Se crea UNA vez con resultado terminal.
    correlation_id vincula Log con sus Attempts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correlation_id = models.UUIDField(db_index=True, help_text='Mismo que NotificationAttempt.correlation_id')
    template = models.ForeignKey(
        NotificationTemplate,
        null=True,
        on_delete=models.SET_NULL,
        related_name='notification_logs'
    )
    event_log_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    expediente_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    proforma_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)

    @property
    def event_log(self):
        return self.resolve_ref('event_log_id')

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    @property
    def proforma(self):
        return self.resolve_ref('proforma_id')
    recipient_email = models.EmailField()
    subject = models.TextField(default='')
    body_preview = models.TextField(max_length=500, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent'),
            ('skipped', 'Skipped'),
            ('disabled', 'Disabled'),
            ('exhausted', 'Exhausted'),
        ]
    )
    error = models.TextField(blank=True, default='')
    trigger_action_source = models.CharField(max_length=32, blank=True, default='')
    template_key = models.CharField(max_length=50, blank=True, default='')
    attempt_count = models.IntegerField(default=1)

    objects = ImmutableManager()

    class Meta:
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(fields=['expediente', '-created_at']),
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['correlation_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['event_log', 'recipient_email'],
                condition=models.Q(event_log__isnull=False),
                name='uniq_notification_per_event_recipient'
            )
        ]

    def delete(self, *args, **kwargs):
        raise PermissionError("NotificationLog is immutable. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and NotificationLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("NotificationLog is immutable. Cannot update.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Log [{self.status}] {self.template_key} → {self.recipient_email}'


# =============================================================================
# C3: CollectionEmailLog — audit trail cobranza automática
# =============================================================================

class CollectionEmailLog(models.Model):
    """
    Audit trail para emails de cobranza automática. Inmutable.
    created_at = timestamp creación. completed_at = cuando se procesó.
    Dedup se basa en completed_at (7 días).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    proforma_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    payment_id = UUIDReferenceField(target_module='finance', null=True, blank=True)

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    @property
    def proforma(self):
        return self.resolve_ref('proforma_id')

    @property
    def payment(self):
        return self.resolve_ref('payment_id')
    created_at = models.DateTimeField(auto_now_add=True)
    grace_days_used = models.IntegerField()
    amount_overdue = models.DecimalField(max_digits=12, decimal_places=2)
    recipient_email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ]
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    objects = ImmutableManager()

    class Meta:
        verbose_name = 'Collection Email Log'
        verbose_name_plural = 'Collection Email Logs'
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        raise PermissionError("CollectionEmailLog is immutable. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and CollectionEmailLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("CollectionEmailLog is immutable. Cannot update.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Collection [{self.status}] → {self.recipient_email}'

from django.db import models
from apps.core.models import TimestampMixin
from django.conf import settings


class ConfigChangeLog(TimestampMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    action = models.CharField(max_length=20)  # create, update, delete
    changes = models.JSONField(default=dict)

    class Meta:
        db_table = 'audit_configchangelog'


class EventLog(TimestampMixin):
    """
    Registro inmutable de eventos de negocio y operaciones del sistema.
    Usado por services comerciales (rebates, artifact_policy, commissions).
    """
    event_type = models.CharField(max_length=100, db_index=True)
    action_source = models.CharField(max_length=100, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='event_logs',
    )
    payload = models.JSONField(default=dict)
    # FK genérica para referenciar cualquier objeto
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'audit_eventlog'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.event_type}] {self.action_source} @ {self.created_at}"

from django.db import models
from django.conf import settings


class ConversationLog(models.Model):
    """Sprint 8 S8-06: Historial de conversaciones con el Knowledge Container."""
    session_id     = models.CharField(max_length=100, db_index=True)
    user           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_logs',
    )
    user_role      = models.CharField(max_length=20)
    expediente_ref = models.ForeignKey(
        'expedientes.ExpedienteSAP',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_logs',
    )
    question    = models.TextField()
    answer      = models.TextField()
    chunks_used = models.JSONField(default=list)
    created_at  = models.DateTimeField(auto_now_add=True)
    retain_until = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Conversation Log'
        verbose_name_plural = 'Conversation Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['retain_until', 'created_at'],
                         name='idx_convlog_retain_created'),
        ]

    def __str__(self):
        return f'Session {self.session_id} — {self.created_at}'

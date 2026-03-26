from django.db import models
from apps.core.models import TimestampMixin
from django.conf import settings

class ConfigChangeLog(TimestampMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    action = models.CharField(max_length=20) # create, update, delete
    changes = models.JSONField(default=dict)

    class Meta:
        db_table = 'audit_configchangelog'

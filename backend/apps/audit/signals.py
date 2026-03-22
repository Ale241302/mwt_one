from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.audit.models import ConfigChangeLog
import json
from django.core.serializers.json import DjangoJSONEncoder

# Tracked models can be registered here. For now, we will track anything that is specified.
TRACKED_MODELS = [
    'BrandClientAgreement', 'BrandClientPriceAgreement', 'AssortmentPolicy', 
    'CreditPolicy', 'PaymentTermPricingVersion', 'BrandWorkflowPolicy'
]

def get_changes(instance, created):
    if created:
        return {'__all__': 'created'}
    # Basic tracking for demonstration. In a real scenario, we'd use pre_save to diff.
    return {'__all__': 'updated'}

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if sender.__name__ in TRACKED_MODELS:
        ConfigChangeLog.objects.create(
            model_name=sender.__name__,
            record_id=str(instance.pk),
            action='create' if created else 'update',
            changes=get_changes(instance, created)
        )

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if sender.__name__ in TRACKED_MODELS:
        ConfigChangeLog.objects.create(
            model_name=sender.__name__,
            record_id=str(instance.pk),
            action='delete',
            changes={'__all__': 'deleted'}
        )

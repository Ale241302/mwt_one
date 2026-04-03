from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pricing.EarlyPaymentPolicy')
def log_early_payment_policy_change(sender, instance, created, **kwargs):
    """
    Registra cambios en EarlyPaymentPolicy en ConfigChangeLog.
    Excepción explícita a S14-C5: esta política es mutable.
    """
    try:
        from apps.core.models import ConfigChangeLog  # import lazy para evitar circular imports
        action = 'created' if created else 'updated'
        ConfigChangeLog.objects.create(
            model_name='EarlyPaymentPolicy',
            object_id=str(instance.pk),
            action=action,
            details={
                'client_subsidiary_id': instance.client_subsidiary_id,
                'brand_id': instance.brand_id,
                'base_payment_days': instance.base_payment_days,
                'base_commission_pct': str(instance.base_commission_pct),
                'is_active': instance.is_active,
            },
        )
    except Exception:
        # Si ConfigChangeLog no existe aún o falla, no rompemos el flujo principal
        pass
